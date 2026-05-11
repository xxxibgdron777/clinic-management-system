from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import RevenuePartner, RevenueShareConfig, RevenueShareCalculation, ReconciliationStatement


@login_required
def partner_list(request):
    partners = RevenuePartner.objects.all()
    return render(request, 'revenue_share/partner_list.html', {
        'partners': partners, 'title': '合作方分成管理'
    })


@login_required
def config_edit(request, pk):
    partner = get_object_or_404(RevenuePartner, pk=pk)
    config, created = RevenueShareConfig.objects.get_or_create(partner=partner)

    if request.method == 'POST':
        config.deduction_rate = Decimal(request.POST.get('deduction_rate', '0.10'))
        config.partner_share_ratio = Decimal(request.POST.get('partner_share_ratio', '0.50'))
        config.deduct_lab_bills = request.POST.get('deduct_lab_bills') == 'on'
        config.deduct_supplements = request.POST.get('deduct_supplements') == 'on'
        config.deduct_imaging = request.POST.get('deduct_imaging') == 'on'
        config.deduct_nurse = request.POST.get('deduct_nurse') == 'on'
        config.deduct_reception = request.POST.get('deduct_reception') == 'on'
        config.deduct_travel = request.POST.get('deduct_travel') == 'on'
        config.deduct_fixed = request.POST.get('deduct_fixed') == 'on'
        config.save()
        messages.success(request, f'{partner.name} 分成配置已更新')
        return redirect('revenue_share:partner_list')

    deduction_fields = [
        ('deduct_lab_bills', '实验室费用'),
        ('deduct_supplements', '保健品费用'),
        ('deduct_imaging', '影像费用'),
        ('deduct_nurse', '护士人工'),
        ('deduct_reception', '客户接待'),
        ('deduct_travel', '差旅费'),
        ('deduct_fixed', '固定费用'),
    ]
    return render(request, 'revenue_share/config_form.html', {
        'partner': partner, 'config': config, 'title': f'分成配置 - {partner.name}',
        'deduction_fields': deduction_fields,
    })


@login_required
def calculation_list(request):
    calculations = RevenueShareCalculation.objects.select_related('partner').all()
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')
    if year:
        calculations = calculations.filter(year=int(year))
    if month:
        calculations = calculations.filter(month=int(month))
    return render(request, 'revenue_share/calculation_list.html', {
        'calculations': calculations, 'title': '分成计算'
    })


@login_required
def calculation_run(request, partner_pk, year, month):
    """Calculate revenue share for a partner in a given month."""
    partner = get_object_or_404(RevenuePartner, pk=partner_pk)
    try:
        config = partner.share_config
    except RevenueShareConfig.DoesNotExist:
        messages.error(request, f'{partner.name} 尚未配置分成规则')
        return redirect('revenue_share:partner_list')

    from apps.vip.models import VIPCostItem

    # Get course revenue for this partner's project
    project_map = {
        'anti_aging': 'anti_aging',
        'lifestyle': 'lifestyle',
        'hormone': 'hormone',
    }
    mapped_project = project_map.get(partner.project, partner.project)

    # Get relevant cost items
    cost_items = VIPCostItem.objects.filter(
        cost_date__year=year, cost_date__month=month,
        # In practice, filter by project type through related fields
    )

    total_revenue = cost_items.aggregate(s=Sum('total_amount'))['s'] or Decimal('0')
    nurse_reception = cost_items.filter(
        cost_type__in=['nurse_labor', 'reception']
    ).aggregate(s=Sum('total_amount'))['s'] or Decimal('0')

    deductions = Decimal('0')
    if config.deduct_lab_bills:
        deductions += cost_items.filter(cost_type='blood_test').aggregate(s=Sum('total_amount'))['s'] or 0
    if config.deduct_imaging:
        deductions += cost_items.filter(cost_type='imaging').aggregate(s=Sum('total_amount'))['s'] or 0
    if config.deduct_nurse:
        deductions += cost_items.filter(cost_type='nurse_labor').aggregate(s=Sum('total_amount'))['s'] or 0
    if config.deduct_reception:
        deductions += cost_items.filter(cost_type='reception').aggregate(s=Sum('total_amount'))['s'] or 0
    if config.deduct_supplements:
        deductions += cost_items.filter(cost_type='supplements').aggregate(s=Sum('total_amount'))['s'] or 0

    nurse_reception_deduction = total_revenue * config.deduction_rate
    total_deductions = deductions + nurse_reception_deduction
    net_revenue = total_revenue - total_deductions
    partner_share = net_revenue * config.partner_share_ratio

    calc, _ = RevenueShareCalculation.objects.update_or_create(
        partner=partner, year=int(year), month=int(month),
        defaults={
            'total_course_revenue': total_revenue,
            'nurse_reception_deduction': nurse_reception_deduction,
            'total_deductions': total_deductions,
            'net_revenue': net_revenue,
            'partner_share': partner_share,
            'status': 'draft',
        }
    )
    messages.success(request, f'{partner.name} {year}-{month} 分成计算完成: {partner_share:,.2f}')
    return redirect('revenue_share:calculation_list')


@login_required
def statement_list(request):
    statements = ReconciliationStatement.objects.select_related('partner').all()
    return render(request, 'revenue_share/statement_list.html', {
        'statements': statements, 'title': '对账单'
    })


@login_required
def statement_generate(request, calc_pk):
    """Generate reconciliation statement from calculation."""
    calc = get_object_or_404(RevenueShareCalculation, pk=calc_pk)
    statement, _ = ReconciliationStatement.objects.update_or_create(
        partner=calc.partner, year=calc.year, month=calc.month,
        defaults={
            'calculation': calc,
            'total_amount': calc.partner_share,
            'statement_data': {
                'total_revenue': float(calc.total_course_revenue),
                'deductions': float(calc.total_deductions),
                'net_revenue': float(calc.net_revenue),
                'partner_share': float(calc.partner_share),
                'deduction_rate': float(calc.partner.share_config.deduction_rate if hasattr(calc.partner, 'share_config') else 0.10),
                'share_ratio': float(calc.partner.share_config.partner_share_ratio if hasattr(calc.partner, 'share_config') else 0.50),
            },
        }
    )
    messages.success(request, f'对账单已生成')
    return redirect('revenue_share:statement_list')
