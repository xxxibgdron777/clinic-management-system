from django.urls import path
from . import views

app_name = 'reports'
urlpatterns = [
    path('', views.report_overview, name='overview'),
    path('edit/', views.report_edit, name='report_edit'),
    path('export/', views.report_export, name='report_export'),
    path('category/<int:category_pk>/', views.category_items, name='category_items'),
]
