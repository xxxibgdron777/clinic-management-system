import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse
from .models import Product, StockIn, StockOut
from .forms import ProductForm, StockInForm, StockOutForm
from apps.core.template_utils import generate_template_excel


def _safe_str(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ''
    return str(val).strip()


@login_required
def product_list(request):
    products = Product.objects.filter(is_active=True)
    query = request.GET.get('q', '')
    if query:
        products = products.filter(
            Q(name_cn__icontains=query) | Q(name_en__icontains=query) |
            Q(supplier__icontains=query)
        )
    return render(request, 'inventory/product_list.html', {
        'products': products, 'query': query, 'title': '商品列表'
    })


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    stock_ins = product.stock_ins.order_by('-created_at')[:50]
    stock_outs = product.stock_outs.order_by('-created_at')[:50]
    return render(request, 'inventory/product_detail.html', {
        'product': product, 'stock_ins': stock_ins, 'stock_outs': stock_outs,
        'title': f'商品详情 - {product.name_cn}'
    })


@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'商品 "{product.name_cn}" 创建成功')
            return redirect('inventory:product_list')
    else:
        form = ProductForm(initial={'selling_price': 0})
    return render(request, 'inventory/product_form.html', {'form': form, 'title': '新增商品'})


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, '商品信息已更新')
            return redirect('inventory:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/product_form.html', {
        'form': form, 'product': product, 'title': f'编辑 - {product.name_cn}'
    })


@login_required
def stock_in_list(request):
    records = StockIn.objects.select_related('product').all()
    return render(request, 'inventory/stock_in_list.html', {
        'records': records, 'title': '入库记录'
    })


@login_required
def stock_in_create(request):
    if request.method == 'POST':
        form = StockInForm(request.POST)
        if form.is_valid():
            stock_in = form.save()
            messages.success(request, f'入库成功: {stock_in.product.name_cn} x{stock_in.quantity}')
            return redirect('inventory:stock_in_list')
    else:
        form = StockInForm()
    return render(request, 'inventory/stock_form_base.html', {'form': form, 'title': '新增入库'})


@login_required
def stock_in_template(request):
    """下载入库Excel模板"""
    return generate_template_excel(
        ['商品名称', '数量', '单价', '类别', '供应商', '批次号'],
        '入库导入模板.xlsx'
    )


@login_required
def stock_in_import(request):
    """Excel批量导入入库"""
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            df = pd.read_excel(excel_file, engine='openpyxl' if excel_file.name.endswith('.xlsx') else 'xlrd')
            success_count = 0
            errors = []
            for idx, row in df.iterrows():
                try:
                    name = _safe_str(row.get('商品名称', row.get('name_cn', '')))
                    qty = int(row.get('数量', row.get('quantity', 0)))
                    price = float(row.get('单价', row.get('unit_price', 0)))
                    if name and qty > 0:
                        product = Product.objects.filter(Q(name_cn=name) | Q(name_en=name)).first()
                        if not product:
                            errors.append(f'第{idx+2}行: 商品"{name}"不存在')
                            continue
                        StockIn.objects.create(
                            product=product, quantity=qty, unit_price=price,
                            type='purchase',
                            supplier=_safe_str(row.get('供应商', row.get('supplier', ''))) or None,
                            batch_number=_safe_str(row.get('批次号', row.get('batch_number', ''))) or '',
                            confirmed=request.POST.get('confirm', 'on') == 'on'
                        )
                        success_count += 1
                except Exception as e:
                    errors.append(f'第{idx+2}行: {str(e)}')
            if success_count:
                messages.success(request, f'成功导入 {success_count} 条入库记录')
            for err in errors[:10]:
                messages.warning(request, err)
        except Exception as e:
            messages.error(request, f'文件读取失败: {str(e)}')
        return redirect('inventory:stock_in_list')
    return render(request, 'inventory/stock_in_import.html', {'title': '批量导入入库'})


@login_required
def stock_out_list(request):
    records = StockOut.objects.select_related('product').all()
    out_type = request.GET.get('out_type', '')
    if out_type:
        records = records.filter(out_type=out_type)
    return render(request, 'inventory/stock_out_list.html', {
        'records': records, 'out_type': out_type, 'title': '出库记录'
    })


@login_required
def stock_out_create(request):
    if request.method == 'POST':
        form = StockOutForm(request.POST)
        if form.is_valid():
            stock_out = form.save()
            messages.success(request, f'出库成功: {stock_out.product.name_cn} x{stock_out.quantity}')
            return redirect('inventory:stock_out_list')
    else:
        form = StockOutForm()
    return render(request, 'inventory/stock_form_base.html', {'form': form, 'title': '新增出库'})


@login_required
def stock_out_export(request):
    """导出出库记录为Excel"""
    records = StockOut.objects.select_related('product').all()
    data = [[
        '日期', '商品名称', '数量', '单价', '总金额', '出库类型', '客户姓名'
    ]]
    for r in records:
        data.append([
            r.created_at.strftime('%Y-%m-%d %H:%M'),
            r.product.name_cn,
            r.quantity,
            float(r.unit_price),
            float(r.total_amount),
            r.get_out_type_display(),
            r.customer_name,
        ])
    df = pd.DataFrame(data[1:], columns=data[0])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=stock_out.xlsx'
    df.to_excel(response, index=False, engine='openpyxl')
    return response
