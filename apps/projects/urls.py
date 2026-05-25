from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('config/<int:pk>/', views.share_config_edit, name='share_config_edit'),
    path('manual-costs/', views.manual_cost_list, name='manual_cost_list'),
    path('manual-costs/create/', views.manual_cost_create, name='manual_cost_create'),
    path('monthly-report/', views.monthly_report, name='monthly_report'),
    path('monthly-report/export/', views.report_export, name='report_export'),
]
