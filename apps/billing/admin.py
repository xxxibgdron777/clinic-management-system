from django.contrib import admin
from .models import BillImport, BillTemplate, GeneratedBill


@admin.register(BillImport)
class BillImportAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'bill_date', 'item_name', 'amount', 'hkd_amount']
    search_fields = ['customer_name', 'item_name']


@admin.register(BillTemplate)
class BillTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'partner_type', 'is_active']


@admin.register(GeneratedBill)
class GeneratedBillAdmin(admin.ModelAdmin):
    list_display = ['partner_name', 'year', 'month', 'total_amount', 'status']
    list_filter = ['status', 'year', 'month']
