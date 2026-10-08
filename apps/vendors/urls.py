from django.urls import path
from django.contrib.auth import views as auth_views
from apps.vendors.views import (
    VendorDashboardView,
    VendorMyBusinessesView,
    VendorAddBusinessView,
    VendorViewBusinessView,
    VendorEditBusinessView,
    VendorImageDeleteView,
    VendorReviewListView,
    approve_review,
    reject_review,
    VendorListingPlansView,
    VendorPurchaseListingPlanView,
    VendorVerifyListingPlanPaymentView,
    VendorAllListingPlansView,
    VendorProfileView,
    VendorPaymentHistoryView,
)

app_name = "vendors"
    
urlpatterns = [
    path("dashboard/", VendorDashboardView.as_view(), name="vendor.dashboard"),
    path("my-businesses/", VendorMyBusinessesView.as_view(), name="my_businesses"),
    path("add-business/", VendorAddBusinessView.as_view(), name="add_business"),
    path("business/<int:pk>/", VendorViewBusinessView.as_view(), name="view_business"),
    path(
        "edit-business/<int:pk>/",
        VendorEditBusinessView.as_view(),
        name="edit_business",
    ),
    path(
        "images/<int:pk>/delete/", VendorImageDeleteView.as_view(), name="delete_image"
    ),
    path("vendor-reviews/", VendorReviewListView.as_view(), name="vendor_reviews"),
    path("vendor-reviews/<int:pk>/approve/", approve_review, name="approve-review"),
    path("vendor-reviews/<int:pk>/reject/", reject_review, name="reject-review"),
    # Business Listing Plans
    path(
        "listing-plans/", VendorAllListingPlansView.as_view(), name="all_listing_plans"
    ),
    path(
        "business/<int:business_pk>/listing-plans/",
        VendorListingPlansView.as_view(),
        name="listing_plans",
    ),
    path(
        "business/<int:business_pk>/listing-plans/<int:plan_pk>/purchase/",
        VendorPurchaseListingPlanView.as_view(),
        name="purchase_listing_plan",
    ),
    path(
        "listing-plans/verify-payment/",
        VendorVerifyListingPlanPaymentView.as_view(),
        name="verify_listing_plan_payment",
    ),
    path("dashboard/", VendorDashboardView.as_view(), name="vendor.dashboard"),
    path("my-businesses/", VendorMyBusinessesView.as_view(), name="my_businesses"),
    path("add-business/", VendorAddBusinessView.as_view(), name="add_business"),
    path("business/<int:pk>/", VendorViewBusinessView.as_view(), name="view_business"),
    path(
        "edit-business/<int:pk>/",
        VendorEditBusinessView.as_view(),
        name="edit_business",
    ),
    path(
        "images/<int:pk>/delete/", VendorImageDeleteView.as_view(), name="delete_image"
    ),
    path("vendor-reviews/", VendorReviewListView.as_view(), name="vendor_reviews"),
    path("vendor-aprove/<int:pk>/approve/", approve_review, name="approve-review"),
    path("vendor-reject/<int:pk>/reject/", reject_review, name="reject-review"),
    path("profile/", VendorProfileView.as_view(), name="vendor_profile"),
    # Payment History
    path(
        "payment-history/", VendorPaymentHistoryView.as_view(), name="payment_history"
    ),
    path("profile/", VendorProfileView.as_view(), name="vendor_profile"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
