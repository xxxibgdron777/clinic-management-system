import pandas as pd
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse
from .models import LabPartner, LabBillRecord, LabBillImportLog
from .forms import LabBillRecordForm, LabBillImportForm, LabBillFilterForm
from apps.core.template_utils import generate_template_excel


@login_required
def record_list(request):
    """实验室账单列表 - 支持多维筛选"""
    records = LabBillRecord.objects.select_related('lab_partner').all()
    filter_form = LabBillFilterForm(request.GET)

    if filter_form.is_valid():
        data = filter_form.cleaned_data
        if data.get('lab_partner'):
            records = records.filter(lab_partner=data['lab_partner'])
        if data.get('customer_name'):
            records = records.filter(customer_name__icontains=data['customer_name'])
        if data.get('date_from'):
            records = records.filter(test_date__gte=data['date_from'])
        if data.get('date_to'):
            records = records.filter(test_date__lte=data['date_to'])
        if data.get('payer'):
            records = records.filter(payer=data['payer'])
        if data.get('department'):
            records = records.filter(department=data['department'])
        if data.get('project'):
            records = records.filter(project=data['project'])

    summary = LabBillRecord.get_filter_summary(records)

    return render(request, 'lab_bills/record_list.html', {
        'records': records,
        'filter_form': filter_form,
        'summary': summary,
        'title': '实验室账单记录'
    })


@login_required
def record_edit(request, pk=None):
    """新增或编辑单条记录"""
    if pk:
        record = get_object_or_404(LabBillRecord, pk=pk)
    else:
        record = None

    if request.method == 'POST':
        form = LabBillRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, '记录已保存')
            return redirect('lab_bills:record_list')
    else:
        form = LabBillRecordForm(instance=record)
    return render(request, 'lab_bills/record_form.html', {
        'form': form, 'record': record, 'title': '编辑记录' if record else '新增记录'
    })


@login_required
def record_import(request):
    """从Excel文件导入实验室账单"""
    if request.method == 'POST':
        form = LabBillImportForm(request.POST, request.FILES)
        if form.is_valid():
            lab_partner = form.cleaned_data['lab_partner']
            excel_file = form.cleaned_data['excel_file']
            skip_duplicates = form.cleaned_data['skip_duplicates']
            default_payer = form.cleaned_data.get('payer', '')
            default_department = form.cleaned_data.get('department', '')
            default_project = form.cleaned_data.get('project', '')

            try:
                df = pd.read_excel(excel_file, engine='openpyxl' if excel_file.name.endswith('.xlsx') else 'xlrd')
            except Exception as e:
                messages.error(request, f'文件读取失败: {str(e)}')
                return render(request, 'lab_bills/record_import.html', {'form': form, 'title': '导入账单'})

            # Column name mapping (handle various column names from different labs)
            col_map = _detect_columns(df.columns.tolist())

            imported, skipped, errors = 0, 0, []

            for idx, row in df.iterrows():
                try:
                    customer = _safe_str(row.get(col_map.get('customer', '')))
                    test_date = _parse_date(row.get(col_map.get('test_date', '')))
                    test_pkg = _safe_str(row.get(col_map.get('test_package', '')))
                    pkg_code = _safe_str(row.get(col_map.get('package_code', '')))
                    qty = int(row.get(col_map.get('quantity', ''), 1) or 1)
                    std_price = float(row.get(col_map.get('standard_price', ''), 0) or 0)
                    disc = float(row.get(col_map.get('discount', ''), 0) or 0)
                    settle_price = float(row.get(col_map.get('settlement_price', ''), 0) or 0)

                    # Read tags from Excel, fallback to form defaults
                    payer = _map_payer(_safe_str(row.get(col_map.get('payer', '')))) or default_payer
                    department = _map_department(_safe_str(row.get(col_map.get('department', '')))) or default_department
                    project_tag = _map_project(_safe_str(row.get(col_map.get('project', '')))) or default_project

                    if not customer:
                        skipped += 1
                        continue

                    # Check duplicates
                    if skip_duplicates:
                        exists = LabBillRecord.objects.filter(
                            lab_partner=lab_partner,
                            customer_name=customer,
                            test_date=test_date,
                            test_package=test_pkg
                        ).exists()
                        if exists:
                            skipped += 1
                            continue

                    LabBillRecord.objects.create(
                        lab_partner=lab_partner,
                        customer_name=customer,
                        test_date=test_date,
                        test_package=test_pkg,
                        package_code=pkg_code,
                        test_quantity=qty,
                        standard_price=std_price,
                        discount=disc,
                        settlement_price=settle_price,
                        payer=payer,
                        department=department,
                        project_tag=project_tag,
                    )
                    imported += 1
                except Exception as e:
                    errors.append(f'第{idx+2}行: {str(e)}')
                    skipped += 1

            # Log the import
            LabBillImportLog.objects.create(
                lab_partner=lab_partner,
                file_name=excel_file.name,
                records_imported=imported,
                records_skipped=skipped,
                errors='\n'.join(errors[:20]) if errors else ''
            )

            messages.success(request, f'导入完成: {imported} 条新增, {skipped} 条跳过')
            if errors:
                messages.warning(request, f'有 {len(errors)} 条错误, 详见导入日志')
            return redirect('lab_bills:record_list')
    else:
        form = LabBillImportForm()

    return render(request, 'lab_bills/record_import.html', {'form': form, 'title': '导入账单'})


@login_required
def record_template(request):
    """下载实验室账单Excel模板"""
    return generate_template_excel(
        ['客户姓名', '检测日期', '检测套餐', '编码', '数量', '标准单价', '折扣', '折后价格', '付款人', '科室', '项目'],
        '实验室账单导入模板.xlsx'
    )


@login_required
def record_export(request):
    """导出筛选后的数据为Excel"""
    records = LabBillRecord.objects.select_related('lab_partner').all()

    # Apply same filters
    f = LabBillFilterForm(request.GET)
    if f.is_valid():
        d = f.cleaned_data
        if d.get('lab_partner'): records = records.filter(lab_partner=d['lab_partner'])
        if d.get('customer_name'): records = records.filter(customer_name__icontains=d['customer_name'])
        if d.get('date_from'): records = records.filter(test_date__gte=d['date_from'])
        if d.get('date_to'): records = records.filter(test_date__lte=d['date_to'])
        if d.get('payer'): records = records.filter(payer=d['payer'])
        if d.get('department'): records = records.filter(department=d['department'])
        if d.get('project'): records = records.filter(project=d['project'])

    data = [[
        '合作方', '检测日期', '客户姓名', '检测套餐', '套餐编码', '检测数量',
        '标准单价', '折扣', '折后价格', '付款人', '科室', '项目', '录入时间'
    ]]
    for r in records:
        data.append([
            r.lab_partner.short_name,
            r.test_date.strftime('%Y-%m-%d') if r.test_date else '',
            r.customer_name, r.test_package, r.package_code,
            r.test_quantity, float(r.standard_price), float(r.discount),
            float(r.settlement_price),
            r.get_payer_display(), r.get_department_display(),
            r.get_project_display(),
            r.created_at.strftime('%Y-%m-%d %H:%M'),
        ])

    df = pd.DataFrame(data[1:], columns=data[0])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=lab_bills.xlsx'
    df.to_excel(response, index=False, engine='openpyxl')
    return response


@login_required
def record_batch_delete(request):
    """批量删除实验室账单记录"""
    if request.method == 'POST':
        ids = request.POST.getlist('record_ids')
        if ids:
            deleted, _ = LabBillRecord.objects.filter(pk__in=ids).delete()
            messages.success(request, f'已删除 {deleted} 条记录')
        else:
            messages.warning(request, '未选择任何记录')
    return redirect('lab_bills:record_list')


@login_required
def partner_list(request):
    partners = LabPartner.objects.all()
    return render(request, 'lab_bills/partner_list.html', {
        'partners': partners, 'title': '合作实验室'
    })


@login_required
def import_logs(request):
    logs = LabBillImportLog.objects.select_related('lab_partner').all()
    return render(request, 'lab_bills/import_logs.html', {
        'logs': logs, 'title': '导入日志'
    })


def _detect_columns(columns):
    """Auto-detect column mapping from various lab formats."""
    mapping = {}
    columns_lower = [c.lower() for c in columns]

    for i, col in enumerate(columns):
        cl = col.lower()
        if any(k in cl for k in ['客户', '姓名', 'customer', 'name', '客户姓名']):
            mapping['customer'] = col
        elif any(k in cl for k in ['检测日期', '日期', 'date', 'test date']):
            mapping['test_date'] = col
        elif any(k in cl for k in ['套餐', '检测项目', 'package', 'test', '项目名称']):
            mapping['test_package'] = col
        elif any(k in cl for k in ['编码', 'code', '套餐编码']):
            mapping['package_code'] = col
        elif any(k in cl for k in ['数量', 'quantity', 'qty']):
            mapping['quantity'] = col
        elif any(k in cl for k in ['标准单价', '标准价格', 'standard', '单价']):
            mapping['standard_price'] = col
        elif any(k in cl for k in ['折扣', 'discount']):
            mapping['discount'] = col
        elif any(k in cl for k in ['结算', '折后', 'settlement', '实际']):
            mapping['settlement_price'] = col
        elif any(k in cl for k in ['付款人', '付款', 'payer', 'payer']):
            mapping['payer'] = col
        elif any(k in cl for k in ['科室', '部门', 'department', 'dept']):
            mapping['department'] = col
        elif any(k in cl for k in ['项目', 'project', '归类']):
            mapping['project'] = col

    return mapping


def _safe_str(val):
    """将Excel值转为字符串，处理NaN"""
    if val is None:
        return ''
    if isinstance(val, float) and pd.isna(val):
        return ''
    return str(val).strip()


def _parse_date(val):
    """Parse date from various formats."""
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None


# --- Tag mapping helpers: 将Excel中的中文标签映射为模型code ---

PAYER_MAP = {
    '个人': 'personal', '泰康': 'taikang', 'MSH': 'msh', 'msh': 'msh',
    '平安': 'pingan', '香港': 'hongkong', '平台工会': 'union', '工会': 'union',
}
DEPT_MAP = {
    '健康管理': 'health_mgmt', '日常医疗': 'daily_med',
}
PROJECT_MAP = {
    '抗衰老': 'anti_aging', '抗衰老首次血检': 'anti_aging_first',
    '生活方式门诊': 'lifestyle', '生活方式门诊首次血检': 'lifestyle_first',
    '荷尔蒙': 'hormone', '荷尔蒙首次血检': 'hormone_first',
    '肠道菌群': 'gut_flora', '阿尔兹海默症': 'alzheimers',
    '血糖代谢检测': 'glucose', '其他常规门诊': 'routine',
}


def _map_payer(label):
    """将付款人中文标签映射为代码"""
    if not label:
        return ''
    # 先尝试直接匹配code
    if label in dict(LabBillRecord.PAYER_CHOICES):
        return label
    return PAYER_MAP.get(label, '')


def _map_department(label):
    if not label:
        return ''
    if label in dict(LabBillRecord.DEPARTMENT_CHOICES):
        return label
    return DEPT_MAP.get(label, '')


def _map_project(label):
    if not label:
        return ''
    if label in dict(LabBillRecord.PROJECT_CHOICES):
        return label
    return PROJECT_MAP.get(label, '')
