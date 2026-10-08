import requests
from ninja import Router
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count
from ninja_jwt.authentication import JWTAuth
from .models import Business, SavedBusiness,BusinessListingPlan
from .schemas import BusinessListSchema, BusinessDetailSchema,BusinessListingPlanSchema

from apps.categories.models import Category, CategoryField

from apps.accounts.auth import CustomJWTAuth

router = Router()

@router.get("/", response=list[BusinessListSchema])
def list_businesses(
    request,
    search: str = None,
    location: str = None,
    category_slug: str = None,
    lat: float = None,
    lng: float = None,
):
    qs = (
    Business.objects.filter(status="verified")
    .select_related("category")
    .prefetch_related("images", "field_values__field")
    .annotate(
        avg_rating=Avg("reviews__rating", filter=Q(reviews__status="approved")),
        review_count=Count("reviews", filter=Q(reviews__status="approved")),
    )
)

    if search:
        qs = qs.filter(
            Q(category__name__icontains=search) | Q(company_name__icontains=search)
        )

    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    if location and not (lat and lng):
        qs_text = qs.filter(
            Q(location__icontains=location) | Q(address__icontains=location)
        )
        if qs_text.exists():
            qs = qs_text
        else:
            from apps.businesses.utils import get_coordinates

            geo_lat, geo_lng = get_coordinates(location)
            if geo_lat and geo_lng:
                lat, lng = geo_lat, geo_lng

    if lat and lng:
        delta = 10 / 111
        qs = qs.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            latitude__range=(lat - delta, lat + delta),
            longitude__range=(lng - delta, lng + delta),
        )

    # Dynamic filters

    for key, value in request.GET.items():
        if key in ["search", "location", "category_slug", "lat", "lng"]:
            continue

        field = CategoryField.objects.filter(
            field_key=key, show_as_filter=True, is_active=True
        ).first()

        if field and value:
            qs = qs.filter(
                field_values__field=field, field_values__value__icontains=value
            )

    if search:
        business_ids = list(qs.values_list("id", flat=True))
        if business_ids:
            from apps.dynamic.models import PopularBusinessSearch
            PopularBusinessSearch.increment_search_bulk(business_ids)

    return qs


@router.post("/favourites/", auth=CustomJWTAuth())
def save_business(request, business_id: int):
    business = get_object_or_404(Business, id=business_id, status="verified")
    saved, created = SavedBusiness.objects.get_or_create(
        user=request.user,
        business=business,
    )
    if created:
        try:
            from apps.notifications.tasks import send_notification_task
            send_notification_task(
                user_id=request.user.id,
                title="Business Saved",
                message=f"You have bookmarked '{business.company_name}' for quick access.",
                channels=["database", "push"]
            )
        except Exception:
            pass
        return {"success": True, "message": "Business saved successfully."}
    return {"success": False, "message": "Business already saved."}


@router.get("/favourites/", auth=CustomJWTAuth())
def get_saved_businesses(request):
    saved = (
        SavedBusiness.objects.filter(user=request.user)
        .select_related("business__category")
        .prefetch_related("business__images")
    )
    return [
        {
            "id": s.id,
            "business_id": s.business.id,
            "company_name": s.business.company_name,
            "slug": s.business.slug,
            "category": s.business.category.name if s.business.category else None,
            "location": s.business.location,
            "phone": s.business.phone,
            "latitude": float(s.business.latitude) if s.business.latitude else None,
            "longitude": float(s.business.longitude) if s.business.longitude else None,
        }
        for s in saved
    ]


@router.delete("/favourites/{saved_id}/", auth=CustomJWTAuth())
def unsave_business(request, saved_id: int):
    saved = get_object_or_404(SavedBusiness, id=saved_id, user=request.user)
    saved.delete()
    return {"success": True, "message": "Business removed from saved."}


@router.get("/{slug}/", response=BusinessDetailSchema)
def get_business(request, slug: str):
    business = get_object_or_404(
        Business.objects.select_related("category").prefetch_related(
            "images", "field_values__field"
        ),
        slug=slug,
        status="verified",
    )
    return business

@router.get("/categories/{slug}/filters/")
def get_category_filters(request, slug: str):
    category = get_object_or_404(Category, slug=slug)

    filters = []

    for field in category.fields.filter(is_active=True, show_as_filter=True):
        filters.append(
            {
                "label": field.label,
                "field_key": field.field_key,
                "field_type": field.field_type,
                "options": field.options or [],
            }
        )

    return filters



# user can see the business plans

@router.get("/business-listing-plans", response=list[BusinessListingPlanSchema])
def business_listing_plans(request):
    return BusinessListingPlan.objects.filter(
        is_active=True
    ).order_by("price")