import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import PaymentRecord, CashRecord
from apps.core.template_utils import generate_template_excel


def _safe_str(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ''
    return str(val).strip()


@login_required
def payment_list(request):
    """List payment records with filtering."""
    records = PaymentRecord.objects.select_related('project__partner').all()
    payment_type = request.GET.get('payment_type', '')
    payer_type = request.GET.get('payer_type', '')
    project_id = request.GET.get('project', '')
    query = request.GET.get('q', '')
    if payment_type:
        records = records.filter(payment_type=payment_type)
    if payer_type:
        records = records.filter(payer_type=payer_type)
    if project_id:
        records = records.filter(project_id=project_id)
    if query:
        records = records.filter(customer_name__icontains=query)
    total = records.aggregate(s=Sum('amount'))['s'] or 0
    from apps.projects.models import Project
    return render(request, 'frontdesk/payment_list.html', {
        'records': records, 'total': total,
        'payment_type': payment_type, 'payer_type': payer_type, 'query': query,
        'project_id': project_id, 'all_projects': Project.objects.filter(is_active=True),
        'title': '前台收款'
    })


@login_required
def payment_template(request):
    """下载收款流水Excel模板"""
    return generate_template_excel(
        ['客户姓名', '收款日期', '金额', '收费项目', '流水号'],
        '收款流水导入模板.xlsx'
    )


@login_required
def payment_import(request):
    """Import payment records from payment platform (通联支付) Excel."""
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            df = pd.read_excel(excel_file)
            imported = 0
            from apps.projects.models import Project
            from apps.vip.models import VIPMember
            for _, row in df.iterrows():
                try:
                    customer = _safe_str(row.get('客户姓名', row.get('customer', '')))
                    proj_name = _safe_str(row.get('收费项目', row.get('归属项目', row.get('project', ''))))
                    project_obj = None
                    if proj_name:
                        project_obj = Project.objects.filter(short_name__iexact=proj_name).first()
                        if not project_obj:
                            project_obj = Project.objects.filter(name__iexact=proj_name).first()
                        if not project_obj:
                            project_obj = Project.objects.filter(name__icontains=proj_name).first()
                    vip = VIPMember.objects.filter(name=customer).first() if customer else None
                    PaymentRecord.objects.create(
                        customer_name=customer,
                        payment_date=pd.to_datetime(row.get('收款日期', row.get('date', ''))).date(),
                        amount=float(row.get('金额', row.get('amount', 0)) or 0),
                        project=project_obj,
                        vip_member=vip,
                        transaction_ref=_safe_str(row.get('流水号', row.get('ref', ''))),
                        source_file=excel_file.name,
                    )
                    imported += 1
                except Exception:
                    continue
            messages.success(request, f'成功导入 {imported} 条收款记录')
        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')
        return redirect('frontdesk:payment_list')
    return render(request, 'frontdesk/payment_import.html', {'title': '导入收款流水'})


@login_required
def payment_create(request):
    """Manually create a payment record."""
    if request.method == 'POST':
        try:
            PaymentRecord.objects.create(
                customer_name=request.POST.get('customer_name', '').strip(),
                payment_date=request.POST.get('payment_date'),
                amount=request.POST.get('amount', 0),
                payment_type=request.POST.get('payment_type', 'outpatient'),
                payer_type=request.POST.get('payer_type', 'self'),
                project_id=request.POST.get('project') or None,
                vip_member_id=request.POST.get('vip_member') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, '收款记录已添加')
        except Exception as e:
            messages.error(request, f'添加失败: {str(e)}')
        return redirect('frontdesk:payment_list')
    from apps.projects.models import Project
    from apps.vip.models import VIPMember
    return render(request, 'frontdesk/payment_form.html', {
        'title': '手动录入收款',
        'projects': Project.objects.filter(is_active=True).select_related('partner'),
        'vip_members': VIPMember.objects.filter(is_active=True),
    })


@login_required
def payment_edit(request, pk):
    """Edit a payment record."""
    record = get_object_or_404(PaymentRecord, pk=pk)
    if request.method == 'POST':
        record.customer_name = request.POST.get('customer_name', record.customer_name)
        record.payment_type = request.POST.get('payment_type', record.payment_type)
        record.payer_type = request.POST.get('payer_type', record.payer_type)
        record.project_id = request.POST.get('project') or None
        record.vip_member_id = request.POST.get('vip_member') or None
        record.notes = request.POST.get('notes', record.notes)
        record.save()
        messages.success(request, '记录已更新')
        return redirect('frontdesk:payment_list')
    from apps.projects.models import Project
    from apps.vip.models import VIPMember
    return render(request, 'frontdesk/payment_edit.html', {
        'record': record, 'title': '编辑收款记录',
        'projects': Project.objects.filter(is_active=True).select_related('partner'),
        'vip_members': VIPMember.objects.filter(is_active=True),
    })


@login_required
def payment_batch_delete(request):
    if request.method == 'POST':
        ids = request.POST.getlist('record_ids')
        if ids:
            deleted, _ = PaymentRecord.objects.filter(pk__in=ids).delete()
            messages.success(request, f'已删除 {deleted} 条收款记录')
        else:
            messages.warning(request, '未选择任何记录')
    return redirect('frontdesk:payment_list')


@login_required
def cash_list(request):
    records = CashRecord.objects.all()
    total_income = records.filter(type='income').aggregate(s=Sum('amount'))['s'] or 0
    total_expense = records.filter(type='expense').aggregate(s=Sum('amount'))['s'] or 0
    return render(request, 'frontdesk/cash_list.html', {
        'records': records, 'total_income': total_income,
        'total_expense': total_expense, 'title': '现金管理'
    })
