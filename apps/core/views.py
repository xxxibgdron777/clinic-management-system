from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    """主仪表盘"""
    from apps.inventory.models import Product, StockOut
    from apps.lab_bills.models import LabBillRecord
    from apps.vip.models import VIPMember

    context = {
        'title': '诊所管理系统',
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_vip_members': VIPMember.objects.filter(is_active=True).count(),
        'total_lab_records': LabBillRecord.objects.count(),
        'recent_stock_outs': StockOut.objects.select_related('product').order_by('-created_at')[:10],
    }
    return render(request, 'dashboard.html', context)
