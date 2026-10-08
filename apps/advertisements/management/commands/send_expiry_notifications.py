import logging
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.advertisements.models import VendorAdvertisementSubscription
from apps.notifications.servicess.notification_service import NotificationService

logger = logging.getLogger(__name__)

# ─── Thresholds ──────────────────────────────────────────────────────────────
# Plans whose total validity is 180+ days (≈6 months / 1 year) get warned
# starting 30 days before expiry.  Shorter plans (e.g. 1 month) get warned
# starting 7 days before expiry.
LONG_PLAN_DAYS = 180          # threshold to classify a plan as "long"
LONG_PLAN_WARN_DAYS = 30      # how many days before expiry to start warning
SHORT_PLAN_WARN_DAYS = 7      # how many days before expiry for short plans


class Command(BaseCommand):

    help = (
        "Send expiry-warning notifications to vendors whose advertisement "
        "subscription is approaching its end date. "
        "Designed to be run daily via a server cron job."
    )

    def handle(self, *args, **kwargs):

        today = date.today()
        now = timezone.now()

        # Only consider active subscriptions that have been activated
        # (i.e. start_date and end_date are set) and have not yet expired.
        subscriptions = VendorAdvertisementSubscription.objects.filter(
            is_active=True,
            start_date__isnull=False,
            end_date__isnull=False,
            end_date__gt=now,
        ).select_related("vendor", "plan")

        notified_count = 0
        skipped_count = 0

        for subscription in subscriptions:

            vendor = subscription.vendor
            plan = subscription.plan

            if not vendor or not plan:
                continue

            # ── Calculate days remaining ──────────────────────────────────
            days_remaining = (subscription.end_date - now).days

            # ── Determine warning window based on plan length ─────────────
            if plan.validity_days >= LONG_PLAN_DAYS:
                warn_window = LONG_PLAN_WARN_DAYS    # 30 days
            else:
                warn_window = SHORT_PLAN_WARN_DAYS   # 7 days

            # Not yet within the warning window — skip silently
            if days_remaining > warn_window:
                continue

            # ── Avoid duplicate notifications on the same calendar day ────
            if subscription.last_expiry_notified_date == today:
                skipped_count += 1
                self.stdout.write(
                    f"[SKIP] {vendor.email} — already notified today "
                    f"(subscription #{subscription.id})."
                )
                continue

            # ── Build notification content ────────────────────────────────
            expiry_date_str = subscription.end_date.strftime("%d %B %Y")

            if days_remaining == 0:
                urgency = "expires TODAY"
            elif days_remaining == 1:
                urgency = "expires TOMORROW"
            else:
                urgency = f"expires in {days_remaining} day(s)"

            title = f"⚠️ Advertisement Plan Expiring Soon — {plan.name}"
            message = (
                f"Hi {vendor.first_name or vendor.email},\n\n"
                f"Your advertisement subscription plan '{plan.name}' {urgency} "
                f"(on {expiry_date_str}).\n\n"
                "Please renew your plan to keep your advertisements running and "
                "maintain your business visibility on JustKlick.\n\n"
                "Thank you for advertising with us!"
            )

            # ── Send through all channels ─────────────────────────────────
            try:
                NotificationService.notify_user(
                    user=vendor,
                    title=title,
                    message=message,
                    channels=["database", "push", "email"],
                )

                # Mark today so we don't re-notify in the same day
                subscription.last_expiry_notified_date = today
                subscription.save(update_fields=["last_expiry_notified_date"])

                notified_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK]   Notified {vendor.email} — "
                        f"'{plan.name}' {urgency} (sub #{subscription.id})."
                    )
                )

            except Exception as exc:
                logger.exception(
                    "Failed to send expiry notification to vendor %s "
                    "for subscription %s: %s",
                    vendor.id,
                    subscription.id,
                    str(exc),
                )
                self.stdout.write(
                    self.style.ERROR(
                        f"[ERR]  Could not notify {vendor.email} "
                        f"(subscription #{subscription.id}): {exc}"
                    )
                )

        # ── Summary ───────────────────────────────────────────────────────
        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone — {notified_count} vendor(s) notified, "
                f"{skipped_count} already notified today."
            )
        )
