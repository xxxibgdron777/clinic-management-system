from django.urls import path
from . import views

app_name = 'lab_bills'
urlpatterns = [
    path('', views.record_list, name='record_list'),
    path('records/', views.record_list, name='record_list'),
    path('records/create/', views.record_edit, name='record_create'),
    path('records/<int:pk>/edit/', views.record_edit, name='record_edit'),
    path('records/import/', views.record_import, name='record_import'),
    path('records/export/', views.record_export, name='record_export'),
    path('records/batch-delete/', views.record_batch_delete, name='record_batch_delete'),
    path('partners/', views.partner_list, name='partner_list'),
    path('logs/', views.import_logs, name='import_logs'),
]
