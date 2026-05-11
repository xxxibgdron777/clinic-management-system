from import_export import resources, fields, widgets
from .models import LabBillRecord, LabPartner


class LabBillRecordResource(resources.ModelResource):
    lab_partner_name = fields.Field(
        attribute='lab_partner__short_name',
        column_name='合作方',
        widget=widgets.ForeignKeyWidget(LabPartner, 'short_name')
    )

    class Meta:
        model = LabBillRecord
        fields = ('lab_partner_name', 'customer_name', 'test_date', 'test_package',
                  'package_code', 'test_quantity', 'standard_price', 'discount',
                  'settlement_price', 'payer', 'department', 'project', 'notes')
        export_order = fields
