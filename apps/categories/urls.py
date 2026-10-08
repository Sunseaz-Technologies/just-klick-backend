from django.urls import path
from apps.categories.views import (
    
    CategoryListView,
    CategoryCreateView,
    CategoryEditView,
    CategoryDeleteView,
    CategoryFieldListView,
    CategoryFieldCreateView,
    CategoryFieldEditView,
    CategoryFieldDeleteView,
)

app_name = 'categories'

urlpatterns = [
    # API endpoints
   

    # Dashboard HTML endpoints
    path('', CategoryListView.as_view(), name='list'),
    path('create/', CategoryCreateView.as_view(), name='create'),
    path('<slug:slug>/edit/', CategoryEditView.as_view(), name='edit'),
    path('<slug:slug>/delete/', CategoryDeleteView.as_view(), name='delete'),

    # Category Field Management
    path('<slug:slug>/fields/', CategoryFieldListView.as_view(), name='fields'),
    path('<slug:slug>/fields/add/', CategoryFieldCreateView.as_view(), name='field_create'),
    path('<slug:slug>/fields/<int:pk>/edit/', CategoryFieldEditView.as_view(), name='field_edit'),
    path('<slug:slug>/fields/<int:pk>/delete/', CategoryFieldDeleteView.as_view(), name='field_delete'),
]