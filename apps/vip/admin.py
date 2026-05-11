from django.contrib import admin
from .models import VIPMember, VIPCourse, VIPPayment, VIPCostItem, VIPRevenueRecognition


@admin.register(VIPMember)
class VIPMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'gender', 'phone', 'is_active', 'created_at']
    search_fields = ['name', 'phone', 'id_number']


@admin.register(VIPCourse)
class VIPCourseAdmin(admin.ModelAdmin):
    list_display = ['member', 'duration_months', 'total_price', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'duration_months']
    search_fields = ['member__name']


@admin.register(VIPPayment)
class VIPPaymentAdmin(admin.ModelAdmin):
    list_display = ['member', 'course', 'amount', 'payment_date', 'project_type']
    list_filter = ['payment_date']
    search_fields = ['member__name']


@admin.register(VIPCostItem)
class VIPCostItemAdmin(admin.ModelAdmin):
    list_display = ['member', 'course', 'cost_type', 'standard_amount', 'cost_amount', 'total_amount']
    list_filter = ['cost_type', 'cost_date']
    search_fields = ['member__name']


@admin.register(VIPRevenueRecognition)
class VIPRevenueRecognitionAdmin(admin.ModelAdmin):
    list_display = ['member', 'course', 'year', 'month', 'revenue_amount', 'is_confirmed']
    list_filter = ['year', 'month', 'is_confirmed']
