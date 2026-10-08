from django.urls import path
from apps.businesses.views import (
    BusinessRegisterView,
    BusinessListView,
    BusinessCreateView,
    BusinessDetailView,
    BusinessEditView,
    BusinessDeleteView,
    BusinessVerifyView,
    BusinessRejectView,
    BusinessImageDeleteView,
    BusinessListingPlanListView,
    BusinessListingPlanCreateView,
    BusinessListingPlanEditView,
    BusinessListingPlanDeleteView,
    AdminBusinessPaymentHistoryView,
    AdminBusinessPaymentExportView,
    AdminPaymentEditView,
    AdminPaymentDetailView
)

app_name = "businesses"

urlpatterns = [
    # Public
    path("register/", BusinessRegisterView.as_view(), name="register"),
    # Admin Dashboard – Business CRUD
    path("", BusinessListView.as_view(), name="list"),
    path("create/", BusinessCreateView.as_view(), name="create"),
    path("<int:pk>/", BusinessDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", BusinessEditView.as_view(), name="edit"),
    path("<int:pk>/delete/", BusinessDeleteView.as_view(), name="delete"),
    path("<int:pk>/verify/", BusinessVerifyView.as_view(), name="verify"),
    path("<int:pk>/reject/", BusinessRejectView.as_view(), name="reject"),
    # Image
    path(
        "images/<int:pk>/delete/",
        BusinessImageDeleteView.as_view(),
        name="delete_image",
    ),
    # Admin Dashboard – Listing Plans CRUD
    path(
        "listing-plans/",
        BusinessListingPlanListView.as_view(),
        name="listing_plan_list",
    ),
    path(
        "listing-plans/create/",
        BusinessListingPlanCreateView.as_view(),
        name="listing_plan_create",
    ),
    path(
        "listing-plans/<int:pk>/edit/",
        BusinessListingPlanEditView.as_view(),
        name="listing_plan_edit",
    ),
    path(
        "listing-plans/<int:pk>/delete/",
        BusinessListingPlanDeleteView.as_view(),
        name="listing_plan_delete",
    ),
    # admin payment history
    path(
        "payment-history/",
        AdminBusinessPaymentHistoryView.as_view(),
        name="payment_history",
    ),
    # admin payment history download url
    path(
        "payment-history/export/",
        AdminBusinessPaymentExportView.as_view(),
        name="payment_history_export",
    ),
    path(
        "admin/payments/<int:pk>/",
        AdminPaymentDetailView.as_view(),
        name="payment_detail",
    ),
    # AJAX edit (pencil modal POSTs here)
    path(
        "admin/payments/<int:pk>/edit/",
        AdminPaymentEditView.as_view(),
        name="payment_edit",
    ),
      path("payments/<int:pk>/edit/", AdminPaymentEditView.as_view(), name="payment_edit"),

   
]