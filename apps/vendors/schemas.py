from ninja import Schema
from typing import List, Optional


class CreateReviewSchema(Schema):
    business_id: int
    rating: float
    review: str


class MessageSchema(Schema):
    success: bool
    message: str


class VendorReviewSchema(Schema):
    id: int
    user: str
    rating: float
    review: str
    status: str
    created_at: str


class VendorReviewListResponseSchema(Schema):
    success: bool
    data: List[VendorReviewSchema]


class PublicReviewSchema(Schema):
    user: str
    rating: float
    review: str
    verified: bool
    date: str


class PublicReviewResponseSchema(Schema):
    success: bool
    data: List[PublicReviewSchema]


class RatingSummarySchema(Schema):
    average_rating: float
    total_reviews: int


class RejectReviewSchema(Schema):
    reason: Optional[str] = None
