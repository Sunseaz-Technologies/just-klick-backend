from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


from django.contrib.auth import views as auth_views
from django.http import HttpResponse

from config.api import api

def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path("health", health_check, name="health_check"),
    path("health/", health_check, name="health_check_slash"),
    path("admin/", admin.site.urls),
    # Authentication
    path("", include("apps.accounts.urls")),
    # Logout
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Dashboard
    path("dashboard/", include("apps.roles.urls")),
    # Categories
    path("dashboard/categories/", include("apps.categories.urls")),
    # Businesses
    path(
        "dashboard/businesses/",
        include("apps.businesses.urls", namespace="businesses"),
    ),
    # vendor dashboard
    path("vendor/", include("apps.vendors.urls", )),
    path("api/", api.urls),
    path("advertisements/", include("apps.advertisements.urls")),
    path("dashboard/dynamic/", include("apps.dynamic.urls" ,namespace="dynamic")),
    
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)