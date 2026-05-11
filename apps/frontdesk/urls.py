from django.urls import path
from . import views

app_name = 'frontdesk'
urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/import/', views.payment_import, name='payment_import'),
    path('payments/<int:pk>/edit/', views.payment_edit, name='payment_edit'),
    path('cash/', views.cash_list, name='cash_list'),
]
