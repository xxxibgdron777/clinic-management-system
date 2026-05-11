from django import forms
from .models import VIPMember, VIPCourse, VIPPayment, VIPCostItem


class VIPMemberForm(forms.ModelForm):
    class Meta:
        model = VIPMember
        fields = ['name', 'gender', 'phone', 'birth_date', 'id_number', 'address', 'notes', 'is_active']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class VIPCourseForm(forms.ModelForm):
    class Meta:
        model = VIPCourse
        fields = ['member', 'duration_months', 'total_price', 'start_date',
                  'attending_doctor', 'status', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class VIPPaymentForm(forms.ModelForm):
    class Meta:
        model = VIPPayment
        fields = ['member', 'course', 'amount', 'payment_date', 'project_type', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class VIPCostItemForm(forms.ModelForm):
    class Meta:
        model = VIPCostItem
        fields = ['member', 'course', 'cost_type', 'custom_name',
                  'standard_amount', 'cost_amount', 'total_amount',
                  'is_per_course', 'cost_date', 'notes']
        widgets = {
            'cost_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class InjectionImportForm(forms.Form):
    """点滴及针剂费用Excel导入表单"""
    member = forms.ModelChoiceField(
        queryset=VIPMember.objects.filter(is_active=True),
        label='VIP会员',
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    course = forms.ModelChoiceField(
        queryset=VIPCourse.objects.all(),
        label='关联疗程',
        required=False,
        help_text='可选，不选则不关联疗程',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    excel_file = forms.FileField(
        label='Excel文件',
        help_text='支持 .xlsx / .xls，需包含：日期、项目名称、数量、单价、金额 等列',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )
    skip_duplicates = forms.BooleanField(
        label='跳过重复',
        required=False, initial=True,
        help_text='同一会员+日期+项目名称的记录将跳过',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
