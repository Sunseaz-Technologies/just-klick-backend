from ninja import Router
from apps.businesses.models import Business
from apps.accounts.models import User
from .models import Review
from .schemas import CreateReviewSchema
from apps.accounts.auth import CustomJWTAuth
from django.db.models import Avg, Count



router = Router()

jwt_auth = CustomJWTAuth()

@router.post("/reviews",auth=jwt_auth)
def create_review(request, payload: CreateReviewSchema):

    business = Business.objects.filter(
        id=payload.business_id
    ).first()

    if not business:
        return {
            "success": False,
            "message": "Business not found"
        }

    Review.objects.create(
        user=request.user,
        business=business,
        rating=payload.rating,
        review=payload.review,
        status="pending"
    )
    if business.user:
        try:
            from apps.notifications.tasks import send_notification_task
            send_notification_task(
                user_id=business.user.id,
                title="New Review Received",
                message=f"A new review was submitted for your business '{business.company_name}' and is pending verification.",
                channels=["database", "push"]
            )
        except Exception:
            pass

    return {
        "success": True,
        "message": "Review submitted successfully"
    }
    
    
@router.get("/business/{business_id}/reviews")
def business_reviews(request, business_id: int):

    reviews = Review.objects.filter(
        business_id=business_id,
        status="approved"
    ).select_related("user")

    return [
        {
            "user": review.user.username,
            "rating": review.rating,
            "review": review.review,
        }
        for review in reviews
    ]
    


@router.get("/total/{business_id}/reviews/count")
def reviews_count(request, business_id: int):

    stats = Review.objects.filter(
        business_id=business_id,
        status="approved"
    ).aggregate(
        average_rating=Avg("rating"),
        total_reviews=Count("id")
    )

    return {
        "average_rating": round(float(stats["average_rating"] or 0), 1),
        "total_reviews": stats["total_reviews"],
       
    }
    
