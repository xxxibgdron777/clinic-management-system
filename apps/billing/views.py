import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import BillImport, BillTemplate, GeneratedBill
from apps.core.template_utils import generate_template_excel


def _safe_str(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ''
    return str(val).strip()


@login_required
def import_list(request):
    imports = BillImport.objects.all()
    return render(request, 'billing/import_list.html', {
        'imports': imports, 'title': 'ABC系统账单导入'
    })


@login_required
def import_template(request):
    """下载ABC账单Excel模板"""
    return generate_template_excel(
        ['客户', '时间', '名称', '单价', '数量', '金额', '港币金额'],
        'ABC账单导入模板.xlsx'
    )


@login_required
def import_upload(request):
    """Upload bill data from ABC system Excel export."""
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            df = pd.read_excel(excel_file, engine='openpyxl' if excel_file.name.endswith('.xlsx') else 'xlrd')
            imported = 0
            for _, row in df.iterrows():
                try:
                    BillImport.objects.create(
                        customer_name=_safe_str(row.get('客户', row.get('customer', ''))),
                        bill_date=pd.to_datetime(row.get('时间', row.get('date', ''))).date(),
                        item_name=_safe_str(row.get('名称', row.get('name', ''))),
                        unit_price=float(row.get('单价', row.get('unit_price', 0)) or 0),
                        quantity=int(row.get('数量', row.get('quantity', 1)) or 1),
                        amount=float(row.get('金额', row.get('amount', 0)) or 0),
                        hkd_amount=float(row.get('港币金额', row.get('hkd', 0)) or 0),
                        source_file=excel_file.name,
                    )
                    imported += 1
                except Exception:
                    continue
            messages.success(request, f'成功导入 {imported} 条记录')
        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')
        return redirect('billing:import_list')
    return render(request, 'billing/import_upload.html', {'title': '导入账单明细'})


@login_required
def template_list(request):
    templates = BillTemplate.objects.all()
    return render(request, 'billing/template_list.html', {
        'templates': templates, 'title': '账单模板'
    })


@login_required
def bill_generate(request, template_pk, year, month):
    """Generate a bill using template and imported data."""
    template = get_object_or_404(BillTemplate, pk=template_pk)
    from django.db.models import Sum as DjSum
    imports = BillImport.objects.filter(bill_date__year=year, bill_date__month=month)

    bill = GeneratedBill.objects.create(
        template=template,
        partner_name=template.partner_type or '合作方',
        year=year, month=month,
        total_amount=imports.aggregate(s=DjSum('amount'))['s'] or 0,
        hkd_total=imports.aggregate(s=DjSum('hkd_amount'))['s'] or 0,
        bill_data={'items': [], 'total_amount': 0},
        status='generated',
    )
    messages.success(request, f'{year}-{month} 账单已生成')
    return redirect('billing:bill_list')


@login_required
def bill_list(request):
    bills = GeneratedBill.objects.all()
    return render(request, 'billing/bill_list.html', {
        'bills': bills, 'title': '已生成账单'
    })
