from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from apps.advertisements.models import (
    Advertisement,
    VendorAdvertisementSubscription
)
from apps.notifications.servicess.notification_service import NotificationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "Delete expired advertisements and notify vendors"

    def handle(self, *args, **kwargs):

        subscriptions = VendorAdvertisementSubscription.objects.filter(
            end_date__lt=timezone.now(),
            is_active=True
        )

        count = 0

        for subscription in subscriptions:

            vendor = subscription.vendor
            plan_name = subscription.plan.name if subscription.plan else "N/A"
            expiry_date_str = subscription.end_date.strftime("%Y-%m-%d") if subscription.end_date else "N/A"

            # Delete associated ads
            Advertisement.objects.filter(subscription=subscription).delete()

            # Deactivate subscription
            subscription.is_active = False
            subscription.save(update_fields=["is_active"])

            # Notify vendor about expiry
            if vendor:
                title = "Your Advertisement Subscription Has Expired"
                message = (
                    f"Your advertisement subscription for plan '{plan_name}' expired on {expiry_date_str}. "
                    "Your advertisements have been removed. "
                    "Please renew your subscription to keep your business visible."
                )
                try:
                    NotificationService.notify_user(
                        user=vendor,
                        title=title,
                        message=message,
                        channels=["database", "push", "email"]
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Notified vendor {vendor.email} about subscription expiry."
                        )
                    )
                except Exception as e:
                    logger.exception(
                        "Failed to send expiry notification to user %s for subscription %s: %s",
                        vendor.id,
                        subscription.id,
                        str(e)
                    )
                    self.stdout.write(
                        self.style.ERROR(
                            f"Error notifying vendor {vendor.email}: {str(e)}"
                        )
                    )

            count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Expired advertisements removed and {count} vendor(s) notified."
            )
        )