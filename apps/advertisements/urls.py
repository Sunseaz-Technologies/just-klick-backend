from django.urls import path

from .views import (
    AdvertisementPlanListView,
    PurchasePlanView,
    AddAdvertisementView,
    EditAdvertisementView,
    MyAdvertisementsView,
    AdvertisementPlanDeleteView,
    AdvertisementPlanEditView,
    AdvertisementPlanCreateView,
    AdvertisementPlanAdminListView,
    AdvertisementEditView,
    AdvertisementDeleteView,
    VerifyPaymentView,
    PaymentHistoryView,
    AdvertisementPaymentAdminListView,
    AdvertisementPaymentExportCSVView,
    AdvertisementAdminDashboardView,
    AdvertisementOrderListView,
    AdvertisementOrderDetailView,
)

app_name = "advertisements"

urlpatterns = [
    path("plans/", AdvertisementPlanListView.as_view(), name="plans"),
    path("purchase/<int:pk>/", PurchasePlanView.as_view(), name="purchase"),
    path("verify-payment/", VerifyPaymentView.as_view(), name="verify_payment"),
    path("add/", AddAdvertisementView.as_view(), name="add_advertisement"),
    path("edit/<int:pk>/", EditAdvertisementView.as_view(), name="edit_advertisement"),
    path("my-ads/", MyAdvertisementsView.as_view(), name="my_ads"),
    path(
        "dashboard/plans/",
        AdvertisementPlanAdminListView.as_view(),
        name="admin_plan_list",
    ),
    path(
        "dashboard/plans/create/",
        AdvertisementPlanCreateView.as_view(),
        name="admin_plan_create",
    ),
    path(
        "dashboard/plans/<int:pk>/edit/",
        AdvertisementPlanEditView.as_view(),
        name="admin_plan_edit",
    ),
    path(
        "dashboard/plans/<int:pk>/delete/",
        AdvertisementPlanDeleteView.as_view(),
        name="admin_plan_delete",
    ),
    path("edit/<int:pk>/", AdvertisementEditView.as_view(), name="edit_advertisement"),
    path(
        "delete/<int:pk>/",
        AdvertisementDeleteView.as_view(),
        name="delete_advertisement",
    ),
    path("payment-history/", PaymentHistoryView.as_view(), name="payment_history"),
    path(
        "admin/payments/",
        AdvertisementPaymentAdminListView.as_view(),
        name="admin_payment_list",
    ),
    path(
        "admin/payments/export-csv/",
        AdvertisementPaymentExportCSVView.as_view(),
        name="advertisement_payment_export_csv",
    ),
    path(
        "dashboard/overview/",
        AdvertisementAdminDashboardView.as_view(),
        name="admin_dashboard",
    ),
    path(
        "dashboard/orders/",
        AdvertisementOrderListView.as_view(),
        name="admin_orders",
    ),
    path(
        "dashboard/orders/<int:pk>/",
        AdvertisementOrderDetailView.as_view(),
        name="admin_order_detail",
    ),
]
