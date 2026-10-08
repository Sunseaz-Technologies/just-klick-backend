from ninja import Schema
from typing import Optional, List
from decimal import Decimal

class BusinessImageSchema(Schema):
    id: int
    image: str

    @staticmethod
    def resolve_image(obj):
        return obj.image.url


class FieldValueSchema(Schema):
    label: str
    field_key: str
    field_type: str
    value: Optional[str] = None

    @staticmethod
    def resolve_label(obj):
        return obj.field.label

    @staticmethod
    def resolve_field_key(obj):
        return obj.field.field_key

    @staticmethod
    def resolve_field_type(obj):
        return obj.field.field_type


class BusinessListSchema(Schema):
    id: int
    company_name: str
    slug: str
    category: Optional[str] = None
    location: str
    phone: Optional[str] = None
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    images: List[BusinessImageSchema] = []
    field_values: List[FieldValueSchema] = []
    avg_rating: float = 0.0
    review_count: int = 0

    @staticmethod
    def resolve_category(obj):
        return obj.category.name if obj.category else None

    @staticmethod
    def resolve_phone(obj):
        if obj.has_active_listing_plan:
            return obj.phone
        return None

    @staticmethod
    def resolve_avg_rating(obj):
        return round(float(getattr(obj, "avg_rating", None) or 0), 1)

    @staticmethod
    def resolve_review_count(obj):
        return getattr(obj, "review_count", 0) or 0


class BusinessDetailSchema(Schema):
    id: int
    company_name: str
    slug: str
    category: Optional[str] = None
    location: str
    address: Optional[str] = None
    email: str
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    images: List[BusinessImageSchema] = []
    field_values: List[FieldValueSchema] = []

    @staticmethod
    def resolve_category(obj):
        return obj.category.name if obj.category else None

    @staticmethod
    def resolve_phone(obj):
        if obj.has_active_listing_plan:
            return obj.phone
        return None

    @staticmethod
    def resolve_whatsapp(obj):
        if obj.has_active_listing_plan:
            return obj.whatsapp
        return None
    


# user can see the business plans
class BusinessListingPlanFeatureSchema(Schema):
    feature: str


class BusinessListingPlanSchema(Schema):
    name: str
    price: Decimal
    validity_days: int
    description: str | None = None
    features: list[str]

    @staticmethod
    def resolve_features(obj):
        return [f.feature for f in obj.features.all()]