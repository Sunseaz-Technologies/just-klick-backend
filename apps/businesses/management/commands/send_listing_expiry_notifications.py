import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.businesses.models import BusinessListingSubscription
from apps.notifications.servicess.notification_service import NotificationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send expiry-warning notifications to vendors whose business listing plans are expiring soon."

    def handle(self, *args, **kwargs):
        now = timezone.now()

        # Fetch active listing subscriptions that have not yet expired
        subscriptions = BusinessListingSubscription.objects.filter(
            is_active=True,
            start_date__isnull=False,
            end_date__isnull=False,
            end_date__gt=now,
        ).select_related("vendor", "plan", "business")

        notified_count = 0

        for subscription in subscriptions:
            vendor = subscription.vendor
            plan = subscription.plan
            business = subscription.business

            if not vendor or not plan or not business:
                continue

            # Calculate remaining days
            days_remaining = (subscription.end_date - now).days

            # Check if they have already purchased/renewed for a future period beyond this subscription's end_date
            has_renewal = BusinessListingSubscription.objects.filter(
                business=business,
                is_active=True,
                payment_status='SUCCESS',
                end_date__gt=subscription.end_date
            ).exists()

            if has_renewal:
                continue

            # Send warnings at specific milestones to avoid spamming the user daily
            if days_remaining not in [7, 3, 1, 0]:
                continue

            expiry_date_str = subscription.end_date.strftime("%d %B %Y")

            if days_remaining == 0:
                urgency = "expires TODAY"
            elif days_remaining == 1:
                urgency = "expires TOMORROW"
            else:
                urgency = f"expires in {days_remaining} days"

            title = f"⚠️ Business Listing Plan Expiring Soon — {business.company_name}"
            message = (
                f"Hi {vendor.first_name or vendor.email},\n\n"
                f"Your listing subscription plan '{plan.name}' for business '{business.company_name}' {urgency} (on {expiry_date_str}).\n\n"
                f"Please renew your subscription to maintain active button unlocks and visibility for your business listing.\n\n"
                "Thank you for listing with JustKlick!"
            )

            try:
                NotificationService.notify_user(
                    user=vendor,
                    title=title,
                    message=message,
                    channels=["database", "push", "email"]
                )
                notified_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] Notified {vendor.email} — business '{business.company_name}' plan {urgency}."
                    )
                )
            except Exception as e:
                logger.exception(f"Failed to send expiry warning to {vendor.email}: {e}")
                self.stdout.write(
                    self.style.ERROR(
                        f"[ERR] Error notifying {vendor.email} for business '{business.company_name}': {e}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done — {notified_count} vendor(s) notified of business listing expiry warnings."
            )
        )
