from django import forms
from .models import LabBillRecord, LabPartner


class LabBillRecordForm(forms.ModelForm):
    class Meta:
        model = LabBillRecord
        fields = ['lab_partner', 'customer_name', 'test_date', 'test_package',
                  'package_code', 'test_quantity', 'standard_price', 'discount',
                  'settlement_price', 'payer', 'department', 'project',
                  'custom_field_1', 'custom_field_2', 'notes']
        widgets = {
            'test_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class LabBillImportForm(forms.Form):
    lab_partner = forms.ModelChoiceField(
        queryset=LabPartner.objects.filter(is_active=True),
        label='合作实验室'
    )
    excel_file = forms.FileField(label='选择账单文件 (.xlsx/.xls)')
    skip_duplicates = forms.BooleanField(
        label='跳过重复记录', required=False, initial=True,
        help_text='同一客户+同一日期+同一套餐视为重复'
    )
    # 导入时可同时设置标签，优先使用Excel中的值，其次使用此处默认值
    payer = forms.ChoiceField(
        label='付款人（默认值）', required=False,
        choices=[('', '---')] + list(LabBillRecord.PAYER_CHOICES),
        help_text='Excel中无此列时使用，也可被Excel中同名列覆盖'
    )
    department = forms.ChoiceField(
        label='科室（默认值）', required=False,
        choices=[('', '---')] + list(LabBillRecord.DEPARTMENT_CHOICES),
        help_text='Excel中无此列时使用'
    )
    project = forms.ChoiceField(
        label='项目（默认值）', required=False,
        choices=[('', '---')] + list(LabBillRecord.PROJECT_CHOICES),
        help_text='Excel中无此列时使用'
    )


class LabBillFilterForm(forms.Form):
    lab_partner = forms.ModelChoiceField(
        queryset=LabPartner.objects.filter(is_active=True),
        label='合作方', required=False
    )
    customer_name = forms.CharField(label='客户姓名', required=False)
    date_from = forms.DateField(label='开始日期', required=False,
        widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(label='结束日期', required=False,
        widget=forms.DateInput(attrs={'type': 'date'}))
    payer = forms.ChoiceField(label='付款人', required=False,
        choices=[('', '---')] + list(LabBillRecord.PAYER_CHOICES))
    department = forms.ChoiceField(label='科室', required=False,
        choices=[('', '---')] + list(LabBillRecord.DEPARTMENT_CHOICES))
    project = forms.ChoiceField(label='项目', required=False,
        choices=[('', '---')] + list(LabBillRecord.PROJECT_CHOICES))
