from django.contrib import admin
from .models import ReportCategory, ReportItem, MonthlyReportEntry


@admin.register(ReportCategory)
class ReportCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_editable', 'is_active']


@admin.register(ReportItem)
class ReportItemAdmin(admin.ModelAdmin):
    list_display = ['category', 'name', 'unit_price', 'is_active']
    list_filter = ['category']


@admin.register(MonthlyReportEntry)
class MonthlyReportEntryAdmin(admin.ModelAdmin):
    list_display = ['report_item', 'year', 'month', 'quantity', 'amount']
    list_filter = ['year', 'month', 'report_item__category']
