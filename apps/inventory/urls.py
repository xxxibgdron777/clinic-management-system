from django.urls import path
from . import views

app_name = 'inventory'
urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('stock-in/', views.stock_in_list, name='stock_in_list'),
    path('stock-in/create/', views.stock_in_create, name='stock_in_create'),
    path('stock-in/import/', views.stock_in_import, name='stock_in_import'),
    path('stock-out/', views.stock_out_list, name='stock_out_list'),
    path('stock-out/create/', views.stock_out_create, name='stock_out_create'),
    path('stock-out/export/', views.stock_out_export, name='stock_out_export'),
]
