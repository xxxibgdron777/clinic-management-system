from django.contrib import admin
from .models import CustomFieldDefinition, CustomFieldValue, SystemConfig


@admin.register(CustomFieldDefinition)
class CustomFieldDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'entity_type', 'field_type', 'is_required', 'order', 'is_active']
    list_filter = ['entity_type', 'field_type', 'is_active']
    search_fields = ['name', 'entity_type']


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'category', 'config_type', 'value', 'updated_at']
    list_filter = ['category', 'config_type']
    search_fields = ['key', 'description']
