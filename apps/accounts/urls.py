from django.urls import path
from .views import *
     
urlpatterns = [
    path("",AdminLoginView.as_view(),name="admin_login"),
    path("forgot-password/",ForgotPasswordView.as_view(),name="forgot_password"),
    path("reset-password/<uidb64>/<token>/",ResetPasswordView.as_view(),name="reset_password"),
    path("logout/",AdminLogoutView.as_view(),name="admin-logout"),
    path("vendor/register/",VendorRegisterView.as_view(),name="vendor-register"),
    path("vendor/login/",VendorLoginView.as_view(),name="vendor-login"),
    path("admin-leads/",LeadListView.as_view(),name="admin-leads"),
    path("delete/<int:pk>/",lead_delete,name="delete"),
    path("trash/",DeletedLeadListView.as_view(),name="trash"),
    path("restore/<int:pk>/",restore_lead,name="restore"),
    path("lead/permanent-delete/<int:pk>/",permanent_delete_lead,name="permanent-delete"),
    path("profile_update/",AdminProfileView.as_view(),name="admin_profile"),
    path("admin-reviews/",AdminReviewListView.as_view(),name="admin-reviews"),
    path("admin-reviews/<int:pk>/approve/",admin_approve_review,name="approve-review"),
    path("admin-reviews/<int:pk>/reject/",admin_reject_review,name="reject-review"),
    path("admin-reviews/<int:pk>/delete/",admin_delete_review,name="delete-review"),
    path("vendor-logout/",VendorLogoutView.as_view(),name="vendor-logout"),
    path("leads/export/", LeadExportCSVView.as_view(), name="lead_export_csv"),
]