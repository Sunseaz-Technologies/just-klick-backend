from django.contrib import admin

# Register your models here.

from apps.businesses.models import Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['id', 'company_name', 'category', 'location', 'email', 'phone', 'status', 'created_at']
    list_filter = ['status', 'category']
    search_fields = ['company_name', 'email', 'phone']
    readonly_fields = [ 'created_at', 'updated_at']