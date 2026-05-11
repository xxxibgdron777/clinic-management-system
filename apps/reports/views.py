import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum
from .models import ReportCategory, ReportItem, MonthlyReportEntry


@login_required
def report_overview(request):
    """Main report view with monthly breakdown."""
    year = int(request.GET.get('year', '')) if request.GET.get('year') else None
    month = int(request.GET.get('month', '')) if request.GET.get('month') else None

    categories = ReportCategory.objects.filter(is_active=True).prefetch_related('items')
    entries = MonthlyReportEntry.objects.all()
    if year:
        entries = entries.filter(year=year)
    if month:
        entries = entries.filter(month=month)

    entries_dict = {}
    for e in entries:
        entries_dict[(e.report_item_id, e.year, e.month)] = e

    report_data = []
    for cat in categories:
        cat_items = []
        for item in cat.items.filter(is_active=True):
            kwargs = {}
            if year: kwargs['year'] = year
            if month: kwargs['month'] = month
            entry = entries_dict.get((item.id, year, month)) if year and month else None
            cat_items.append({
                'item': item,
                'entry': entry,
                'amount': entry.amount if entry else 0,
                'quantity': entry.quantity if entry else 0,
            })
        total = sum(i['amount'] for i in cat_items)
        report_data.append({'category': cat, 'items': cat_items, 'total': total})

    return render(request, 'reports/overview.html', {
        'report_data': report_data, 'year': year, 'month': month,
        'title': '每月报表'
    })


@login_required
def report_edit(request):
    """Inline editor for report entries (supports sport/nervous rehab)."""
    if request.method == 'POST':
        item_pk = request.POST.get('item_pk')
        year = int(request.POST.get('year', 0))
        month = int(request.POST.get('month', 0))
        quantity = int(request.POST.get('quantity', 0))
        amount = request.POST.get('amount', '0')
        notes = request.POST.get('notes', '')

        entry, _ = MonthlyReportEntry.objects.update_or_create(
            report_item_id=item_pk, year=year, month=month,
            defaults={'quantity': quantity, 'amount': amount, 'notes': notes}
        )
        messages.success(request, '数据已保存')
        return redirect(request.GET.get('next', 'reports:overview'))

    return redirect('reports:overview')


@login_required
def report_export(request):
    """Export report data to Excel."""
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')

    entries = MonthlyReportEntry.objects.select_related(
        'report_item__category'
    ).all()
    if year: entries = entries.filter(year=int(year))
    if month: entries = entries.filter(month=int(month))

    data = [['分类', '项目', '年份', '月份', '数量', '金额']]
    for e in entries:
        data.append([
            e.report_item.category.name,
            e.report_item.name,
            e.year, e.month, e.quantity, float(e.amount)
        ])
    df = pd.DataFrame(data[1:], columns=data[0])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=monthly_report.xlsx'
    df.to_excel(response, index=False, engine='openpyxl')
    return response


@login_required
def category_items(request, category_pk):
    """Manage report items within a category."""
    category = get_object_or_404(ReportCategory, pk=category_pk)
    items = category.items.all()
    return render(request, 'reports/category_items.html', {
        'category': category, 'items': items, 'title': f'{category.name} - 项目管理'
    })
