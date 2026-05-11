from django.contrib import admin
from .models import RevenuePartner, RevenueShareConfig, RevenueShareCalculation, ReconciliationStatement


@admin.register(RevenuePartner)
class RevenuePartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'contact_person', 'is_active']


@admin.register(RevenueShareConfig)
class RevenueShareConfigAdmin(admin.ModelAdmin):
    list_display = ['partner', 'deduction_rate', 'partner_share_ratio']


@admin.register(RevenueShareCalculation)
class RevenueShareCalculationAdmin(admin.ModelAdmin):
    list_display = ['partner', 'year', 'month', 'total_course_revenue',
                    'net_revenue', 'partner_share', 'status']
    list_filter = ['status', 'year', 'month']


@admin.register(ReconciliationStatement)
class ReconciliationStatementAdmin(admin.ModelAdmin):
    list_display = ['partner', 'year', 'month', 'total_amount', 'status']
    list_filter = ['status', 'year', 'month']
