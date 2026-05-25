from django.contrib import admin
from .models import Partner, Project, CostCategory, ProjectCategoryConfig, RevenueShareConfig, RevenueShareConfigHistory


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'contact_phone', 'is_active']
    search_fields = ['name']


class ProjectCategoryConfigInline(admin.TabularInline):
    model = ProjectCategoryConfig
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'partner', 'project_type', 'unit_price', 'duration_months', 'is_active']
    list_filter = ['partner', 'project_type']
    inlines = [ProjectCategoryConfigInline]


@admin.register(CostCategory)
class CostCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_system', 'is_active']


@admin.register(RevenueShareConfig)
class RevenueShareConfigAdmin(admin.ModelAdmin):
    list_display = ['project', 'share_ratio', 'nurse_fee_rate']
    list_filter = ['project__partner']
    filter_horizontal = ['deductible_categories']


@admin.register(RevenueShareConfigHistory)
class RevenueShareConfigHistoryAdmin(admin.ModelAdmin):
    list_display = ['project', 'share_ratio', 'nurse_fee_rate', 'changed_at']
    list_filter = ['project__partner']
