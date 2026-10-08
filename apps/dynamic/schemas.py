from ninja import Schema
from typing import List, Optional
from datetime import datetime
    
class WhyChooseUssSchema(Schema):
    """Response schema for simple WhyChooseUss items (list endpoint)."""

    id: int
    title: str
    description: str
    icon: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str

class FAQCreateSchema(Schema):
    question: str
    answer: str
    is_active: bool = True


class FAQUpdateSchema(Schema):
    question: Optional[str] = None
    answer: Optional[str] = None
    is_active: Optional[bool] = None


# --- About Section ---
class AboutSchema(Schema):
    id: int
    section_tag: str
    main_title: str
    main_description: str
    button_text: str
    button_link: str
    about_image: Optional[str] = None
    top_badge_text: str
    trust_card_title: str
    trust_card_subtitle: str

    visitors_icon: str
    visitors_count: str
    visitors_label: str

    students_icon: str
    students_count: str
    students_label: str

    businesses_icon: str
    businesses_count: str
    businesses_label: str

    feature_one_icon: str
    feature_one_title: str
    feature_two_icon: str
    feature_two_title: str
    feature_three_icon: str
    feature_three_title: str


    is_active: bool
    @staticmethod
    def resolve_about_image(obj):
        return obj.about_image.url if obj.about_image else None


# --- Promise Section ---
class PromiseCardSchema(Schema):
    id: int
    icon: str
    title: str
    description: str
    display_order: int
    is_active: bool


class PromiseSectionSchema(Schema):
    id: int
    section_name: str
    title: str
    description: str
    is_active: bool
    cards: List[PromiseCardSchema] = []

    @staticmethod
    def resolve_cards(obj):
        # Retrieve all active cards for this section
        return list(obj.cards.filter(is_active=True))

# who we are

class CounterSchema(Schema):
    count: str
    label: str

class PopularServiceSchema(Schema):
    name: str


class ValueItemSchema(Schema):
    icon: str
    title: str
    description: str


class WhoWeAreSchema(Schema):
    who_we_are_badge: str
    hero_title: str
    hero_description: str

    mission_icon: str
    mission_title: str
    mission_description: str

    popular_services_title: str
    popular_services_sub: str

    our_values_badge: str
    values_title: str
    values_description: str

    counters: List[CounterSchema]
    services: List[PopularServiceSchema]
    value_items: List[ValueItemSchema]
    
    

# --- Partner Section ---
class PartnerImageSchema(Schema):
    id: int
    image: Optional[str] = None

    @staticmethod
    def resolve_image(obj):
        return obj.image.url if obj.image else None


class BulkPartnerSectionSchema(Schema):
    id: int
    section_name: str
    title: str
    description: str
    is_active: bool
    images: List[PartnerImageSchema] = []

    @staticmethod
    def resolve_images(obj):
        return list(obj.images.all())


# --- Team Section ---
class TeamSectionSchema(Schema):
    id: int
    section_name: str
    title: str
    description: str
    image: Optional[str] = None
    name: str
    role: str
    member_description: str
    is_active: bool

    @staticmethod
    def resolve_image(obj):
        return obj.image.url if obj.image else None





class HomePageSchema(Schema):
    about: Optional[AboutSchema] = None
    promise: Optional[PromiseSectionSchema] = None
    who_we_are: Optional[WhoWeAreSchema] = None
    partners: List[BulkPartnerSectionSchema] = []
    team: List[TeamSectionSchema] = []





class ContactFeatureSchema(Schema):

    id: int

    icon: str

    title: str

    value: str


class ContactFormFieldSchema(Schema):

    id: int

    label: str

    placeholder: str

    field_type: str

    required: bool


class ContactPageSchema(Schema):

    id: int

    title: str

    description: str

    form_title: str

    button_text: str

    map_iframe: str

    features: List[ContactFeatureSchema] = []

    form_fields: List[ContactFormFieldSchema] = []

    @staticmethod
    def resolve_features(obj):

        return list(obj.features.filter(is_active=True))

    @staticmethod
    def resolve_form_fields(obj):

        return list(obj.form_fields.all())


class ContactEnquirySchema(Schema):

    full_name: str

    email: str

    phone: str

    subject: str

    message: str


class ContactEnquiryResponseSchema(Schema):

    id: int

    full_name: str

    email: str

    phone: str

    subject: str

    message: str


class TouristPlaceSchema(Schema):
    id: int
    title: str
    location: str
    description: str
    rating: float
  
    image: str | None


# --- Popular Nearby Services/Businesses ---
class NearbyBusinessImageSchema(Schema):
    id: int
    image: Optional[str] = None

    @staticmethod
    def resolve_image(obj):
        return obj.image.url if obj.image else None


class NearbyBusinessSchema(Schema):
    """Schema for businesses near user's current location"""

    id: int
    company_name: str
    slug: str
    category: Optional[str] = None
    location: str
    phone: str
    email: str
    address: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str
    distance: Optional[float] = None  # Distance in kilometers
    images: List[NearbyBusinessImageSchema] = []

    @staticmethod
    def resolve_category(obj):
        return obj.category.name if obj.category else None

    @staticmethod
    def resolve_images(obj):
        return list(obj.images.all()[:5])  # Return first 5 images


class PopularNearbyServiceSchema(Schema):
    """Grouped response for popular services by category"""

    category: Optional[str] = None
    listings_count: int
    businesses: List[NearbyBusinessSchema] = []

    image: str | None


# --- Popular Searches/Categories ---

class BusinessListingSchema(Schema):
    """Summary schema for a business listing shown inside popular searches"""

    id: int
    company_name: str
    slug: str
    category: Optional[str] = None
    location: str
    phone: str
    address: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None

    @staticmethod
    def resolve_category(obj):
        return obj.category.name if obj.category else None

    @staticmethod
    def resolve_image(obj):
        first_image = obj.images.first()
        return first_image.image.url if first_image and first_image.image else None


class PopularSearchSchema(Schema):
    """Schema for popular category searches with top business listings"""

    id: int
    category_name: str
    category_slug: str
    category_image: Optional[str] = None
    search_count: int
    listings_count: int
    display_order: int
    is_featured: bool
    top_listings: List[BusinessListingSchema] = []

    @staticmethod
    def resolve_category_name(obj):
        return obj.category.name

    @staticmethod
    def resolve_category_slug(obj):
        return obj.category.slug

    @staticmethod
    def resolve_category_image(obj):
        return obj.category.image.url if obj.category.image else None

    @staticmethod
    def resolve_listings_count(obj):
        from apps.businesses.models import Business
        return Business.objects.filter(category=obj.category, status="verified").count()

    @staticmethod
    def resolve_top_listings(obj):
        from apps.businesses.models import Business
        return list(
            Business.objects.filter(category=obj.category, status="verified")
            .prefetch_related("images")
            .order_by("-created_at")[:5]
        )


class CategoryListingSchema(Schema):
    """Simple category listing with count"""

    id: int
    name: str
    slug: str
    image: Optional[str] = None
    listings_count: int

    @staticmethod
    def resolve_image(obj):
        return obj.image.url if obj.image else None

    @staticmethod
    def resolve_listings_count(obj):
        from apps.businesses.models import Business

        return Business.objects.filter(category=obj, status="verified").count()


class ContactEnquirySchema(Schema):
    full_name: str
    email: str
    phone: str
    subject: str
    message: str

# terms and conditions
class LegalPageOutSchema(Schema):
    id: int
    title: str
    content: str
    is_active: bool
    updated_at: datetime


class PopularBusinessSearchSchema(Schema):
    """Schema for popular business searches"""

    id: int
    business_id: int
    company_name: str
    slug: str
    search_count: int
    display_order: int
    is_featured: bool
    status: str
    image: Optional[str] = None

    @staticmethod
    def resolve_business_id(obj):
        return obj.business.id

    @staticmethod
    def resolve_company_name(obj):
        return obj.business.company_name

    @staticmethod
    def resolve_slug(obj):
        return obj.business.slug

    @staticmethod
    def resolve_image(obj):
        first_image = obj.business.images.first()
        return first_image.image.url if first_image and first_image.image else None