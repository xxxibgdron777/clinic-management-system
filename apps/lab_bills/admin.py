from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import LabPartner, LabBillRecord, LabBillImportLog
from .resources import LabBillRecordResource


@admin.register(LabPartner)
class LabPartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'contact_person', 'contact_phone', 'is_active']


@admin.register(LabBillRecord)
class LabBillRecordAdmin(ImportExportModelAdmin):
    resource_class = LabBillRecordResource
    list_display = ['lab_partner', 'customer_name', 'test_date', 'test_package',
                    'standard_price', 'discount', 'settlement_price', 'payer', 'project', 'created_at']
    list_filter = ['lab_partner', 'payer', 'department', 'project', 'test_date']
    search_fields = ['customer_name', 'test_package', 'package_code']
    date_hierarchy = 'test_date'
    list_per_page = 50  # 减少单页记录数，避免超出DATA_UPLOAD_MAX_NUMBER_FIELDS限制


@admin.register(LabBillImportLog)
class LabBillImportLogAdmin(admin.ModelAdmin):
    list_display = ['lab_partner', 'file_name', 'records_imported', 'imported_at']
    list_filter = ['lab_partner']
