from django.db import models
from apps.accounts.models import User
from apps.businesses.models import Business


class Review(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    review = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    vendor_verified = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business.name} - {self.rating}"
