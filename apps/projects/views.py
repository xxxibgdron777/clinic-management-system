from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum
from .models import (Partner, Project, CostCategory, ProjectCategoryConfig,
                     RevenueShareConfig, ManualCostEntry, MonthlyReport,
                     calculate_monthly_report)
import pandas as pd


@login_required
def project_list(request):
    partners = Partner.objects.filter(is_active=True).prefetch_related('projects')
    return render(request, 'projects/project_list.html', {
        'partners': partners, 'title': '合作商与项目管理'
    })


@login_required
def share_config_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    config, _ = RevenueShareConfig.objects.get_or_create(project=project)
    categories = CostCategory.objects.filter(is_active=True)
    if request.method == 'POST':
        config.share_ratio = Decimal(request.POST.get('share_ratio', '0.50'))
        # 表单发的是百分比数（如10=10%），除以100转为小数
        nurse_val = Decimal(request.POST.get('nurse_fee_rate', '10'))
        config.nurse_fee_rate = (nurse_val / 100).quantize(Decimal('0.0001'))
        config.save()
        config.save_history()
        selected_ids = request.POST.getlist('deductible_categories')
        config.deductible_categories.set(selected_ids)
        messages.success(request, f'{project} 分成配置已更新')
        return redirect('projects:project_list')
    selected_ids = list(config.deductible_categories.values_list('id', flat=True))
    nurse_cat = categories.filter(name='护士服务费').first()
    return render(request, 'projects/share_config_form.html', {
        'project': project, 'config': config, 'categories': categories,
        'selected_ids': selected_ids, 'nurse_cat_id': nurse_cat.pk if nurse_cat else 0,
        'nurse_fee_pct': round(float(config.nurse_fee_rate) * 100, 1),
        'share_ratio_pct': round(float(config.share_ratio) * 100),
        'title': f'分成配置 - {project}'
    })


# ==================== 手工费用 ====================

@login_required
def manual_cost_list(request):
    entries = ManualCostEntry.objects.select_related('project', 'category').all()
    project_id = request.GET.get('project', '')
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')
    if project_id:
        entries = entries.filter(project_id=project_id)
    if year:
        entries = entries.filter(cost_date__year=int(year))
    if month:
        entries = entries.filter(cost_date__month=int(month))
    total = entries.aggregate(s=Sum('amount'))['s'] or Decimal('0')
    return render(request, 'projects/manual_cost_list.html', {
        'entries': entries, 'total': total, 'title': '手工费用录入',
        'projects': Project.objects.filter(is_active=True),
    })


@login_required
def manual_cost_create(request):
    if request.method == 'POST':
        try:
            ManualCostEntry.objects.create(
                project_id=request.POST.get('project'),
                category_id=request.POST.get('category'),
                amount=request.POST.get('amount', 0),
                cost_date=request.POST.get('cost_date'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, '费用已录入')
        except Exception as e:
            messages.error(request, f'录入失败: {str(e)}')
        return redirect('projects:manual_cost_list')
    projects = Project.objects.filter(is_active=True)
    categories = CostCategory.objects.filter(is_active=True)
    return render(request, 'projects/manual_cost_form.html', {
        'projects': projects, 'categories': categories, 'title': '新增手工费用'
    })


# ==================== 月度报表 ====================

@login_required
def monthly_report(request):
    year = int(request.GET.get('year', '')) if request.GET.get('year') else None
    month = int(request.GET.get('month', '')) if request.GET.get('month') else None
    project_id = request.GET.get('project', '')

    projects = Project.objects.filter(is_active=True)
    if project_id:
        projects = projects.filter(pk=project_id)

    reports = []
    for proj in projects:
        if year and month:
            # 为选定的年月生成/刷新报表
            rpt = calculate_monthly_report(proj, year, month)
            reports.append(rpt)
        else:
            # 显示所有已有报表
            qs = MonthlyReport.objects.filter(project=proj)
            if year:
                qs = qs.filter(year=year)
            if month:
                qs = qs.filter(month=month)
            reports.extend(list(qs))

    # 按项目+年月排序
    reports.sort(key=lambda r: (str(r.project), -r.year, -r.month))

    return render(request, 'projects/monthly_report.html', {
        'reports': reports, 'year': year, 'month': month, 'title': '月度报表',
        'projects': Project.objects.filter(is_active=True),
        'project_id': project_id,
    })


@login_required
def report_export(request):
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')
    project_id = request.GET.get('project', '')

    reports = MonthlyReport.objects.all()
    if year:
        reports = reports.filter(year=int(year))
    if month:
        reports = reports.filter(month=int(month))
    if project_id:
        reports = reports.filter(project_id=project_id)

    data = [['项目', '年份', '月份', '收入合计', '费用合计', '毛利', '应付分成']]
    for r in reports:
        data.append([str(r.project), r.year, r.month,
                     float(r.total_income), float(r.total_cost),
                     float(r.gross_profit), float(r.share_amount)])
    df = pd.DataFrame(data[1:], columns=data[0])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=monthly_report.xlsx'
    df.to_excel(response, index=False, engine='openpyxl')
    return response
