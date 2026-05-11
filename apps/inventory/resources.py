from import_export import resources, fields
from .models import Product, StockIn, StockOut


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        import_id_fields = ['name_cn']
        fields = ('name_cn', 'name_en', 'category', 'unit', 'cost_price',
                  'selling_price', 'supplier', 'current_stock', 'expiry_date',
                  'batch_number', 'barcode', 'is_active')
        export_order = fields


class StockInResource(resources.ModelResource):
    product_name = fields.Field(attribute='product__name_cn', column_name='商品名称')

    class Meta:
        model = StockIn
        fields = ('product_name', 'quantity', 'unit_price', 'total_amount',
                  'type', 'supplier', 'batch_number', 'notes', 'created_at')
        export_order = fields


class StockOutResource(resources.ModelResource):
    product_name = fields.Field(attribute='product__name_cn', column_name='商品名称')

    class Meta:
        model = StockOut
        fields = ('product_name', 'quantity', 'unit_price', 'total_amount',
                  'out_type', 'customer_name', 'notes', 'created_at')
        export_order = fields
