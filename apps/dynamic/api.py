from ninja import Router
from apps.businesses.models import Business
from django.db.models import Q, F, Count
from math import radians, cos, sin, asin, sqrt
from typing import Optional
from .models import (
    AboutSection,
    PromiseSection,
    BulkPartnerSection,
    TeamSection,
    FAQ,
    WhyChooseUss,
    ContactPage,
    ContactEnquiry,
    TouristPlace,
    PopularSearch,
    PopularBusinessSearch,
    WhoWeAreSection,
    TermsAndConditions, 
    PrivacyPolicy
)

from django.http import Http404
from .schemas import (
    ContactPageSchema,
    ContactEnquirySchema,
    ContactEnquiryResponseSchema,
    TouristPlaceSchema,
    NearbyBusinessSchema,
    PopularNearbyServiceSchema,
    HomePageSchema,
    WhyChooseUssSchema,
    PopularSearchSchema,
    PopularBusinessSearchSchema,
    BusinessListingSchema,
    CategoryListingSchema,
    WhoWeAreSchema,
     LegalPageOutSchema,
)

router = Router(tags=["Sections"])


# Helper function to calculate distance using Haversine formula
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(
        radians, [float(lat1), float(lon1), float(lat2), float(lon2)]
    )

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


# Popular Nearby Services/Businesses Endpoints


@router.get("/popular-near-you/", response=list[NearbyBusinessSchema])
def popular_near_you(
    request,
    latitude: float,
    longitude: float,
    radius: float = 10.0,  # Default 10 km radius
    category_id: Optional[int] = None,
    limit: int = 50,
):
    """
    Get popular services/businesses near the user's current location.

    Query Parameters:
    - latitude: User's current latitude (required)
    - longitude: User's current longitude (required)
    - radius: Search radius in kilometers (default: 10km)
    - category_id: Filter by category ID (optional)
    - limit: Maximum number of results to return (default: 50)

    Returns: List of verified businesses sorted by distance (closest first)
    """

    # Filter verified businesses only
    query = Business.objects.filter(
        status="verified", latitude__isnull=False, longitude__isnull=False
    )

    # Apply category filter if provided
    if category_id:
        query = query.filter(category_id=category_id)

    # Calculate distance for each business and filter by radius
    businesses_with_distance = []

    for business in query:
        distance = haversine_distance(
            latitude, longitude, business.latitude, business.longitude
        )

        # Only include businesses within the specified radius
        if distance <= radius:
            businesses_with_distance.append(
                {"business": business, "distance": round(distance, 2)}
            )

    # Sort by distance (closest first), then by newest first
    businesses_with_distance.sort(key=lambda x: (x["distance"], -x["business"].id))

    # Prepare response data with distance
    result = []
    for item in businesses_with_distance[:limit]:
        business = item["business"]
        business.distance = item["distance"]
        result.append(business)

    return result


@router.get("/popular-searches/", response=list[PopularSearchSchema])
def popular_searches(request, limit: int = 10):
    """
    Get most searched categories with their top business listings.

    Query Parameters:
    - limit: Number of popular categories to return

    Returns:
    - Category details
    - Search count
    - Number of verified listings
    - Top 5 verified business listings
    """

    popular = (
        PopularSearch.objects.filter(category__is_active=True)
        .select_related("category")
        .order_by("-is_featured", "-search_count", "display_order")[:limit]
    )

    return popular


@router.get("/popular-businesses/", response=list[PopularBusinessSearchSchema])
def popular_businesses(request, limit: int = 10):
    """
    Get most searched businesses that have been verified and approved by the admin.

    Query Parameters:
    - limit: Number of popular business searches to return

    Returns:
    - Business details
    - Search count
    - Verification status
    """
    popular = (
        PopularBusinessSearch.objects.filter(status="approved", business__status="verified")
        .select_related("business", "business__category")
        .prefetch_related("business__images")
        .order_by("-is_featured", "-search_count", "display_order")[:limit]
    )
    return popular

@router.get("/why-choose-us/", response=list[WhyChooseUssSchema])
def why_choose_us_list(request):
    """
    List all active "Why Choose Us" items with icons.
    Returns: List of WhyChooseUss items ordered by newest first.
    """
    items = []
    for item in WhyChooseUss.objects.all().order_by("-id"):
        try:
            icon_url = item.icon.url if item.icon else None
        except (AttributeError, ValueError):
            # Handle cases where icon file might be missing or invalid
            icon_url = None

        items.append(
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "icon": icon_url,
                "is_active": item.is_active,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }
        )

    return items


# FAQS
@router.get("/faqs/")
# List
def faq_list(request):

    return [
        {
            "id": item.id,
            "question": item.question,
            "answer": item.answer,
            "is_active": item.is_active,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        for item in FAQ.objects.all().order_by("-id")
    ]


@router.get("/about", response=HomePageSchema)
def homepage(request):
    return {
        "about": AboutSection.objects.filter(is_active=True).first(),
        "promise": PromiseSection.objects.prefetch_related("cards")
        .filter(is_active=True)
        .first(),
        "partners": BulkPartnerSection.objects.prefetch_related("images").filter(
            is_active=True
        ),
        "team": TeamSection.objects.filter(is_active=True),
        "who_we_are": (
            WhoWeAreSection.objects.prefetch_related(
                "counters", "services", "value_items"
            )
            .filter(is_active=True)
            .first()
        ),
    }


@router.get("/contact-page")
def contact_page(request):

    contact = ContactPage.objects.filter(is_active=True).first()

    if not contact:
        return {
            "success": False,
            "message": "Contact page not found"
        }

    return {
        "success": True,
        "data": {
            "id": contact.id,
            "title": contact.title,
            "description": contact.description,
            "form_title": contact.form_title,
            "button_text": contact.button_text,
            "map_iframe": contact.map_iframe,
            "features": [
                {
                    "id": feature.id,
                    "icon": feature.icon,
                    "title": feature.title,
                    "value": feature.value,
                    "display_order": feature.display_order,
                }
                for feature in contact.features.filter(is_active=True)
            ],
        },
    }


@router.post("/contact-submit")
def contact_submit(request, payload: ContactEnquirySchema):

    ContactEnquiry.objects.create(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        subject=payload.subject,
        message=payload.message,
    )

    return {"success": True, "message": "Message submitted successfully"}


@router.get("/contact-enquiries", response=list[ContactEnquiryResponseSchema])
def contact_enquiries(request):

    return ContactEnquiry.objects.all().order_by("-id")


@router.get("/tourist-places/", response=list[TouristPlaceSchema])
def tourist_places(request):

    places = TouristPlace.objects.filter(is_active=True).order_by("-id")

    return [
        {
            "id": place.id,
            "title": place.title,
            "location": place.location,
            "description": place.description,
            "rating": float(place.rating),
            "image": place.image.url if place.image else None,
        }
        for place in places
    ]





# terms and conditions sections

@router.get("/terms", response=LegalPageOutSchema)
def get_active_terms(request):
    """Retrieves the latest active version of the Terms & Conditions."""
    term_page = TermsAndConditions.objects.filter(is_active=True).first()
    if not term_page:
        raise Http404("No active Terms & Conditions document found.")
    return term_page

@router.get("/privacy", response=LegalPageOutSchema)
def get_active_privacy(request):
    """Retrieves the latest active version of the Privacy Policy."""
    privacy_page = PrivacyPolicy.objects.filter(is_active=True).first()
    if not privacy_page:
        raise Http404("No active Privacy Policy document found.")
    return privacy_page