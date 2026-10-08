from ninja import Schema
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

class AdvertisementPlanOut(Schema):
    id: int
    name: str
    price: Decimal
    validity_days: int
    is_active: bool

class PurchasePlanOut(Schema):
    success: bool
    razorpay_order_id: str
    amount: int  # in paise
    currency: str
    razorpay_key_id: str
    user_email: str
    user_phone: str
    user_name: str

class VerifyPaymentIn(Schema):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str

class VerifyPaymentOut(Schema):
    success: bool
    message: str

class AdvertisementOut(Schema):
    id: int
    image: str
    redirect_url: str
    created_at: datetime

    @staticmethod
    def resolve_image(obj):
        return obj.image.url if obj.image else ""

class SubscriptionOut(Schema):
    id: int
    plan_name: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool
    is_valid: bool
    remaining_days: Optional[int] = None

    @staticmethod
    def resolve_plan_name(obj):
        return obj.plan.name if obj.plan else ""

    @staticmethod
    def resolve_is_valid(obj):
        return obj.subscription_active()

    @staticmethod
    def resolve_remaining_days(obj):
        from django.utils import timezone
        if obj.start_date and obj.end_date:
            return max(0, (obj.end_date - timezone.now()).days)
        return None

class MyAdvertisementsOut(Schema):
    subscription: Optional[SubscriptionOut] = None
    advertisements: List[AdvertisementOut]



# user can see the ads plans
class AdvertisementPlanSchema(Schema):
    name: str
    price: Decimal
    validity_days: int
    features: list[str]

    @staticmethod
    def resolve_features(obj):
        return [f.feature for f in obj.features.all()]