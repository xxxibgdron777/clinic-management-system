from django import forms
from .models import Product, StockIn, StockOut


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name_cn', 'name_en', 'category', 'unit', 'cost_price',
                  'selling_price', 'expiry_date', 'supplier', 'current_stock',
                  'min_stock_threshold', 'batch_number', 'barcode', 'notes', 'is_active']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class StockInForm(forms.ModelForm):
    class Meta:
        model = StockIn
        fields = ['product', 'quantity', 'unit_price', 'type', 'supplier',
                  'batch_number', 'expiry_date', 'notes', 'confirmed']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class StockOutForm(forms.ModelForm):
    project = forms.ModelChoiceField(
        queryset=None, label='归属项目', required=True,
        help_text='必选：6个合作项目之一'
    )
    class Meta:
        model = StockOut
        fields = ['product', 'quantity', 'unit_price', 'out_type',
                  'customer_name', 'project', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.projects.models import Project
        self.fields['project'].queryset = Project.objects.filter(is_active=True)


class StockInImportForm(forms.Form):
    excel_file = forms.FileField(label='选择Excel文件')
    confirm = forms.BooleanField(label='确认导入并更新库存', required=False, initial=True)
