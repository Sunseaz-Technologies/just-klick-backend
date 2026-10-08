from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("roles/", views.roles, name="roles"),
    path("roles/delete/<int:role_id>/", views.delete_role, name="delete_role"),
    path("roles/add/", views.add_new_role, name="newrole"),
    path("permissions/<int:role_id>/", views.permissions, name="permissions"),
    path("users/", views.users, name="users"),
    path("students/", views.student_list, name="student_list"),
    path("students/<int:user_id>/", views.student_details, name="student_details"),
    path("students/edit/<int:user_id>/",views.edit_student,name="edit_student",),
    path("users/block/<int:user_id>/", views.block_user, name="block_user"),
    path("users/unblock/<int:user_id>/", views.unblock_user, name="unblock_user"),
    path("users/delete/<int:user_id>/", views.delete_user, name="delete_user"),
    path("users/create/", views.create_user, name="create_user"),
    path("vendors-list/", views.vendor_list, name="vendor_list"),
    path("vendors/export/", views.vendor_export_csv, name="vendor_export_csv"),
]
