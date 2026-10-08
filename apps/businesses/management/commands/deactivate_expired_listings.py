import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.businesses.models import BusinessListingSubscription
from apps.notifications.servicess.notification_service import NotificationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Deactivate expired business listing subscriptions and notify vendors."

    def handle(self, *args, **kwargs):
        now = timezone.now()

        # Find subscriptions that are past their end date but still marked as active
        expired_subscriptions = BusinessListingSubscription.objects.filter(
            is_active=True,
            end_date__lt=now
        ).select_related("vendor", "plan", "business")

        count = 0

        for subscription in expired_subscriptions:
            vendor = subscription.vendor
            plan = subscription.plan
            business = subscription.business

            if not vendor or not plan or not business:
                continue

            # Deactivate subscription
            subscription.is_active = False
            subscription.save(update_fields=["is_active"])

            # Check if there is still another active subscription for this business to avoid false notifications
            has_other_active = BusinessListingSubscription.objects.filter(
                business=business,
                is_active=True,
                payment_status='SUCCESS',
                end_date__gt=now
            ).exists()

            if has_other_active:
                continue

            expiry_date_str = subscription.end_date.strftime("%d %B %Y")

            title = f"🔴 Your Business Listing Plan Has Expired — {business.company_name}"
            message = (
                f"Hi {vendor.first_name or vendor.email},\n\n"
                f"Your listing subscription plan '{plan.name}' for business '{business.company_name}' expired on {expiry_date_str}.\n\n"
                f"Due to the plan expiration, contact details (phone and WhatsApp buttons) on your business listing have been locked for clients.\n\n"
                f"Please renew your subscription to unlock contact buttons and restore full visibility for your listing.\n\n"
                "Thank you for listing with JustKlick!"
            )

            try:
                NotificationService.notify_user(
                    user=vendor,
                    title=title,
                    message=message,
                    channels=["database", "push", "email"]
                )
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] Deactivated and notified {vendor.email} for business '{business.company_name}'."
                    )
                )
            except Exception as e:
                logger.exception(f"Failed to send expiration notification to {vendor.email}: {e}")
                self.stdout.write(
                    self.style.ERROR(
                        f"[ERR] Error notifying {vendor.email} for business '{business.company_name}': {e}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done — Deactivated {count} expired business listing subscription(s) and notified vendors."
            )
        )
