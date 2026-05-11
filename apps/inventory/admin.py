from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Product, StockIn, StockOut
from .resources import ProductResource, StockInResource, StockOutResource


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = ['name_cn', 'name_en', 'unit', 'cost_price', 'selling_price',
                    'current_stock', 'supplier', 'expiry_date', 'is_active']
    list_filter = ['category', 'is_active', 'supplier']
    search_fields = ['name_cn', 'name_en', 'supplier', 'barcode']
    list_editable = ['selling_price', 'current_stock']


@admin.register(StockIn)
class StockInAdmin(ImportExportModelAdmin):
    resource_class = StockInResource
    list_display = ['product', 'quantity', 'unit_price', 'total_amount',
                    'type', 'supplier', 'confirmed', 'created_at']
    list_filter = ['type', 'confirmed', 'created_at']
    search_fields = ['product__name_cn', 'supplier']
    date_hierarchy = 'created_at'


@admin.register(StockOut)
class StockOutAdmin(ImportExportModelAdmin):
    resource_class = StockOutResource
    list_display = ['product', 'quantity', 'unit_price', 'total_amount',
                    'out_type', 'customer_name', 'created_at']
    list_filter = ['out_type', 'created_at']
    search_fields = ['product__name_cn', 'customer_name']
    date_hierarchy = 'created_at'
