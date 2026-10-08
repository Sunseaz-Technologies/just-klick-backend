from django.db import models
from django.utils.text import slugify
from apps.accounts.models import User
from apps.categories.models import Category, CategoryField
class Business(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    ]
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="businesses",
    )
    company_name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="businesses",
    )
    description = models.TextField(null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    location = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    whatsapp = models.CharField(max_length=15, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    rejection_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Businesses"
        ordering = ["-created_at"]

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.company_name)
            slug = base_slug
            counter = 1
            while Business.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if self.location:
            from apps.businesses.utils import get_coordinates

            lat, lng = get_coordinates(self.location)
            self.latitude = lat
            self.longitude = lng

        super().save(*args, **kwargs)

    @property
    def has_active_listing_plan(self):
        from django.utils import timezone

        now = timezone.now()
        return self.listing_subscriptions.filter(
            is_active=True,
            payment_status="SUCCESS",
            start_date__lte=now,
            end_date__gte=now,
        ).exists()


class BusinessImage(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="businesses/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.business.company_name}"


class BusinessFieldValue(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="field_values",
    )
    field = models.ForeignKey(
        CategoryField,
        on_delete=models.CASCADE,
        related_name="values",
    )
    value = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("business", "field")
        verbose_name = "Business Field Value"
        verbose_name_plural = "Business Field Values"

    def __str__(self):
        return f"{self.business.company_name} - {self.field.label}: {self.value}"


class SavedBusiness(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="saved_businesses",
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="saved_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "business")

    def __str__(self):
        return f"{self.user} saved {self.business.company_name}"


# ─────────────────────────────────────────────
# Business Listing Plans  (contact-unlock plans)
# ─────────────────────────────────────────────


class BusinessListingPlan(models.Model):
    """
    Admin-managed plans that unlock phone / WhatsApp contact buttons
    for clients viewing a business listing.
    Examples: Monthly (30 days), Quarterly (90 days), Yearly (365 days).
    """

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    validity_days = models.PositiveIntegerField()
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["price"]

    def __str__(self):
        return f"{self.name} – ₹{self.price} / {self.validity_days} days"
    
class BusinessListingPlanFeature(models.Model):
    plan = models.ForeignKey(
        BusinessListingPlan,
        on_delete=models.CASCADE,
        related_name="features"
    )
    feature = models.CharField(max_length=255)

    def __str__(self):
        return self.feature
    
    
    

class BusinessListingSubscription(models.Model):
    """
    Tracks which businesses have an active listing plan.
    One subscription per purchase; a new row is created on each renewal.
    """

    from django.conf import settings as _settings

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="listing_subscriptions",
    )
    plan = models.ForeignKey(
        BusinessListingPlan,
        on_delete=models.CASCADE,
    )
    vendor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="listing_subscriptions",
    )

    # Razorpay payment details
    razorpay_order_id = models.CharField(max_length=255, unique=True)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=500, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(
        max_length=20,
        choices=[("PENDING", "Pending"), ("SUCCESS", "Success"), ("FAILED", "Failed")],
        default="PENDING",
    )

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.business.company_name} – {self.plan.name}"

    @property
    def subscription_active(self):
        from django.utils import timezone

        if not self.start_date or not self.end_date:
            return False
        if self.end_date <= timezone.now():
            if self.is_active:
                self.is_active = False
                self.save(update_fields=["is_active"])
            return False
        return True
