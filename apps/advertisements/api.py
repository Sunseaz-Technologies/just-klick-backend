from ninja import Router, File, Form
from ninja.files import UploadedFile
from ninja_jwt.authentication import JWTAuth

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
import razorpay

from .models import (
    AdvertisementPlan,
    VendorAdvertisementSubscription,
    Advertisement,
    AdvertisementPayment
)
from .schemas import (
    AdvertisementPlanOut,
    PurchasePlanOut,
    VerifyPaymentIn,
    VerifyPaymentOut,
    AdvertisementOut,
    MyAdvertisementsOut,
    AdvertisementPlanSchema
)

# Initialize Razorpay Client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

router = Router(tags=["Advertisements"])


@router.get("", response=list[AdvertisementOut])
def list_active_advertisements(request):

    now = timezone.now()
    active_ads = Advertisement.objects.filter(
        subscription__is_active=True,
        subscription__start_date__isnull=False,
        subscription__end_date__gt=now
    ).order_by("-created_at")

    return list(active_ads)



# user can see ads plans
@router.get("/advertisement-plans", response=list[AdvertisementPlanSchema])
def advertisement_plans(request):
    return AdvertisementPlan.objects.filter(
        is_active=True
    ).order_by("price").prefetch_related("features")
