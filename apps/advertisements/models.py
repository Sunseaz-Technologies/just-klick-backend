from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class AdvertisementPlan(models.Model):

    name = models.CharField(max_length=100)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    validity_days = models.PositiveIntegerField()

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class AdvertisementPlanFeature(models.Model):
    plan = models.ForeignKey(
        AdvertisementPlan,
        on_delete=models.CASCADE,
        related_name="features"
    )
    feature = models.CharField(max_length=255)

    def __str__(self):
        return self.feature


class VendorAdvertisementSubscription(models.Model):

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="advertisement_subscriptions"
    )

    plan = models.ForeignKey(
        AdvertisementPlan,
        on_delete=models.CASCADE
    )

    start_date = models.DateTimeField(
        null=True,
        blank=True
    )

    end_date = models.DateTimeField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    # Tracks the last date an expiry-warning notification was sent.
    # Used by the send_expiry_notifications management command to avoid
    # sending duplicate alerts when the cron job runs more than once a day.
    last_expiry_notified_date = models.DateField(
        null=True,
        blank=True
    )

    # Notification tracking flags to avoid sending duplicate alerts
    notification_14_days_sent = models.BooleanField(default=False)
    notification_7_days_sent = models.BooleanField(default=False)
    notification_1_day_sent = models.BooleanField(default=False)

    def activate_subscription(self):

        if self.start_date:
            return

        self.start_date = timezone.now()

        self.end_date = (
            self.start_date +
            timedelta(days=self.plan.validity_days)
        )

        self.save()

    @property
    def subscription_active(self):

        if not self.start_date or not self.end_date:
            return False

        if self.end_date <= timezone.now():

            if self.is_active:
                self.is_active = False
                self.save(update_fields=["is_active"])

            return False

        return True


class Advertisement(models.Model):

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    subscription = models.ForeignKey(
        VendorAdvertisementSubscription,
        on_delete=models.CASCADE
    )

    image = models.ImageField(
        upload_to="advertisements/"
    )

    redirect_url = models.URLField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.vendor.email


class AdvertisementPayment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="advertisement_payments"
    )

    plan = models.ForeignKey(
        AdvertisementPlan,
        on_delete=models.CASCADE
    )

    razorpay_order_id = models.CharField(max_length=255, unique=True)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=500, null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vendor.email} - {self.plan.name} - {self.status}"
