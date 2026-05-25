import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import VIPMember, VIPCourse, VIPPayment, VIPCostItem
from .forms import VIPMemberForm, VIPCourseForm, VIPPaymentForm, VIPCostItemForm, InjectionImportForm
from apps.core.template_utils import generate_template_excel


def _safe_str(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ''
    return str(val).strip()


@login_required
def member_import(request):
    """批量导入会员"""
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            df = pd.read_excel(excel_file)

            # 在列名中搜索关键词（支持带括号的列名如"会员姓名(必填)"）
            def col(*keywords):
                for c in df.columns:
                    for kw in keywords:
                        if kw in str(c):
                            return c
                return None

            name_col = col('会员姓名', '姓名', '客户姓名', '名称')
            number_col = col('档案号', '会员编号', '编号')
            phone_col = col('电话')
            gender_col = col('性别')
            birth_col = col('出生日期', '生日')

            imported, skipped = 0, 0
            for _, row in df.iterrows():
                name = _safe_str(row.get(name_col)) if name_col else ''
                number = _safe_str(row.get(number_col)) if number_col else ''
                if not name:
                    skipped += 1
                    continue
                phone = _safe_str(row.get(phone_col)) if phone_col else ''
                gender = 'F' if '女' in _safe_str(row.get(gender_col)) else 'M' if gender_col else 'M'
                birth = None
                if birth_col:
                    try:
                        bd_val = row.get(birth_col)
                        if pd.notna(bd_val):
                            birth = pd.to_datetime(bd_val).date()
                    except Exception:
                        pass
                # 档案号格式化为6位数字
                if number and number.isdigit():
                    number = str(int(number)).zfill(6)
                # 去重：已有同名同号则跳过
                if number and VIPMember.objects.filter(member_number=number).exists():
                    skipped += 1
                    continue
                VIPMember.objects.create(
                    name=name, member_number=number, phone=phone,
                    gender=gender, birth_date=birth,
                )
                imported += 1
            messages.success(request, f'导入完成: {imported} 条，跳过 {skipped} 条')
        except Exception as e:
            messages.error(request, f'导入失败: {str(e)}')
        return redirect('vip:member_list')
    return render(request, 'vip/member_import.html', {'title': '批量导入会员'})


@login_required
def member_list(request):
    members = VIPMember.objects.all()
    return render(request, 'vip/member_list.html', {
        'members': members, 'title': 'VIP会员列表'
    })


@login_required
def member_detail(request, pk):
    member = get_object_or_404(VIPMember, pk=pk)
    courses = member.courses.all()
    payments = member.frontdesk_payments.order_by('-payment_date')
    lab_bills = member.lab_bill_records.select_related('lab_partner').order_by('-test_date')
    stock_outs = member.stock_outs.select_related('product').order_by('-created_at')[:20]
    cost_items = member.cost_items.select_related('course').all()
    total_revenue = payments.aggregate(s=Sum('amount'))['s'] or 0
    return render(request, 'vip/member_detail.html', {
        'member': member, 'courses': courses, 'payments': payments,
        'lab_bills': lab_bills, 'stock_outs': stock_outs,
        'cost_items': cost_items, 'total_revenue': total_revenue,
        'title': f'会员详情 - {member.name}'
    })


@login_required
def member_create(request):
    if request.method == 'POST':
        form = VIPMemberForm(request.POST)
        if form.is_valid():
            form.save(); messages.success(request, '会员创建成功')
            return redirect('vip:member_list')
    else:
        form = VIPMemberForm()
    return render(request, 'vip/member_form.html', {'form': form, 'title': '新增会员'})


@login_required
def member_edit(request, pk):
    member = get_object_or_404(VIPMember, pk=pk)
    if request.method == 'POST':
        form = VIPMemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save(); messages.success(request, '会员信息已更新')
            return redirect('vip:member_detail', pk=pk)
    else:
        form = VIPMemberForm(instance=member)
    return render(request, 'vip/member_form.html', {
        'form': form, 'member': member, 'title': f'编辑 - {member.name}'
    })


@login_required
def course_list(request):
    courses = VIPCourse.objects.select_related('member').all()
    return render(request, 'vip/course_list.html', {
        'courses': courses, 'title': '疗程列表'
    })


@login_required
def course_create(request):
    if request.method == 'POST':
        form = VIPCourseForm(request.POST)
        if form.is_valid():
            form.save(); messages.success(request, '疗程创建成功')
            return redirect('vip:course_list')
    else:
        form = VIPCourseForm()
    return render(request, 'vip/generic_form.html', {'form': form, 'title': '新增疗程'})


@login_required
def payment_list(request):
    payments = VIPPayment.objects.select_related('member', 'course').all()
    return render(request, 'vip/payment_list.html', {
        'payments': payments, 'title': '收款记录'
    })


@login_required
def payment_create(request):
    if request.method == 'POST':
        form = VIPPaymentForm(request.POST)
        if form.is_valid():
            form.save(); messages.success(request, '收款记录已添加')
            return redirect('vip:payment_list')
    else:
        form = VIPPaymentForm()
    return render(request, 'vip/generic_form.html', {'form': form, 'title': '新增收款'})


@login_required
def cost_item_list(request, course_pk=None):
    items = VIPCostItem.objects.select_related('member', 'course').all()
    if course_pk:
        items = items.filter(course_id=course_pk)
    return render(request, 'vip/cost_item_list.html', {
        'items': items, 'title': '疗程费用项'
    })


@login_required
def cost_item_create(request):
    if request.method == 'POST':
        form = VIPCostItemForm(request.POST)
        if form.is_valid():
            form.save(); messages.success(request, '费用项已添加')
            return redirect('vip:cost_item_list')
    else:
        form = VIPCostItemForm()
    return render(request, 'vip/generic_form.html', {'form': form, 'title': '新增费用项'})


@login_required
def injection_template(request):
    """下载点滴费用Excel模板"""
    return generate_template_excel(
        ['日期', '项目名称', '数量', '单价', '金额'],
        '点滴费用导入模板.xlsx'
    )


@login_required
def injection_import(request):
    """从Excel导入点滴及针剂费用"""
    if request.method == 'POST':
        form = InjectionImportForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.cleaned_data['member']
            course = form.cleaned_data['course']
            excel_file = form.cleaned_data['excel_file']
            skip_duplicates = form.cleaned_data['skip_duplicates']

            try:
                ext = excel_file.name.rsplit('.', 1)[-1].lower()
                engine = 'openpyxl' if ext == 'xlsx' else 'xlrd'
                df = pd.read_excel(excel_file, engine=engine)
            except Exception as e:
                messages.error(request, f'文件读取失败: {str(e)}')
                return render(request, 'vip/injection_import.html', {'form': form, 'title': '导入点滴及针剂费用'})

            col_map = _detect_injection_columns(df.columns.tolist())

            imported, skipped, errors = 0, 0, []

            for idx, row in df.iterrows():
                try:
                    item_name = _safe_str(row.get(col_map.get('item_name', '')))
                    cost_date = _parse_injection_date(row.get(col_map.get('cost_date', '')))
                    qty = float(row.get(col_map.get('quantity', ''), 1) or 1)
                    unit_price = float(row.get(col_map.get('unit_price', ''), 0) or 0)
                    total = float(row.get(col_map.get('total_amount', ''), 0) or 0)

                    if not item_name:
                        skipped += 1
                        continue

                    # Auto-calculate total if not provided
                    if not total and unit_price and qty:
                        total = unit_price * qty

                    if skip_duplicates:
                        exists = VIPCostItem.objects.filter(
                            member=member,
                            cost_type='injection',
                            custom_name=item_name,
                            cost_date=cost_date,
                        ).exists()
                        if exists:
                            skipped += 1
                            continue

                    VIPCostItem.objects.create(
                        member=member,
                        course=course,
                        cost_type='injection',
                        custom_name=item_name,
                        standard_amount=unit_price,
                        cost_amount=unit_price,
                        total_amount=total,
                        cost_date=cost_date,
                    )
                    imported += 1
                except Exception as e:
                    errors.append(f'第{idx+2}行: {str(e)}')
                    skipped += 1

            messages.success(request, f'导入完成: {imported} 条新增, {skipped} 条跳过')
            if errors:
                messages.warning(request, f'有 {len(errors)} 条错误: {errors[:5]}')
            return redirect('vip:cost_item_list')
    else:
        form = InjectionImportForm()

    return render(request, 'vip/injection_import.html', {'form': form, 'title': '导入点滴及针剂费用'})


def _detect_injection_columns(columns):
    """自动检测点滴导入Excel的列映射"""
    mapping = {}
    for col in columns:
        cl = col.lower()
        if any(k in cl for k in ['项目', '名称', 'item', 'name', '药品', '针剂', '点滴']):
            mapping['item_name'] = col
        elif any(k in cl for k in ['日期', 'date']):
            mapping['cost_date'] = col
        elif any(k in cl for k in ['数量', 'quantity', 'qty']):
            mapping['quantity'] = col
        elif any(k in cl for k in ['单价', 'unit', 'price']):
            mapping['unit_price'] = col
        elif any(k in cl for k in ['金额', '总价', 'amount', 'total', '费用']):
            mapping['total_amount'] = col
    return mapping


def _parse_injection_date(val):
    """解析日期"""
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None
