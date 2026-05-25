"""
Module: 合作商与项目管理 + 统一费用科目库 + 手工费用 + 月度报表
Central entities: Partner → Project → CostCategory
"""
from django.db import models
from django.db.models import Sum, Q
from decimal import Decimal
from apps.core.models import TimeStampedModel


class Partner(models.Model):
    """合作商（香港巴黎/叶医生/杨医生）"""
    name = models.CharField('合作商名称', max_length=100, unique=True)
    contact_person = models.CharField('联系人', max_length=50, blank=True)
    contact_phone = models.CharField('联系电话', max_length=30, blank=True)
    notes = models.TextField('备注', blank=True)
    is_active = models.BooleanField('启用', default=True)

    class Meta:
        db_table = 'project_partner'
        verbose_name = '合作商'
        verbose_name_plural = verbose_name
        ordering = ['name']

    def __str__(self):
        return self.name


class Project(models.Model):
    """合作项目（每个合作商2个项目：首次血检 + 疗程管理）"""
    TYPE_CHOICES = [
        ('first_test', '首次血检'),
        ('course_mgmt', '疗程管理'),
    ]
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='projects', verbose_name='合作商')
    name = models.CharField('项目名称', max_length=100)
    project_type = models.CharField('项目类型', max_length=20, choices=TYPE_CHOICES)
    unit_price = models.DecimalField('单价', max_digits=12, decimal_places=2, default=0,
        help_text='首次血检:检测费单价; 疗程管理:疗程总价')
    duration_months = models.IntegerField('疗程时长(月)', default=1,
        help_text='仅疗程管理有效，首次血检固定为1')
    order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('启用', default=True)

    class Meta:
        db_table = 'project_project'
        verbose_name = '合作项目'
        verbose_name_plural = verbose_name
        ordering = ['partner', 'order']
        unique_together = ['partner', 'name']

    def __str__(self):
        return f'{self.partner.name} - {self.name}'

    @property
    def display_name(self):
        return str(self)

    @property
    def monthly_revenue(self):
        """每月应确认收入（仅疗程管理有效）"""
        if self.project_type == 'course_mgmt' and self.duration_months > 0:
            return self.unit_price / self.duration_months
        return self.unit_price


class CostCategory(models.Model):
    """统一费用科目库（全局共用）"""
    name = models.CharField('科目名称', max_length=50, unique=True)
    description = models.TextField('说明', blank=True)
    is_system = models.BooleanField('系统内置', default=False,
        help_text='系统内置科目不可删除')
    order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('启用', default=True)

    class Meta:
        db_table = 'project_cost_category'
        verbose_name = '费用科目'
        verbose_name_plural = verbose_name
        ordering = ['order']

    def __str__(self):
        return self.name


class ProjectCategoryConfig(models.Model):
    """项目-科目关联配置（每个项目启用哪些科目）"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='category_configs', verbose_name='项目')
    category = models.ForeignKey(CostCategory, on_delete=models.CASCADE, related_name='project_configs', verbose_name='科目')
    is_enabled = models.BooleanField('启用', default=True)

    class Meta:
        db_table = 'project_category_config'
        verbose_name = '项目科目配置'
        verbose_name_plural = verbose_name
        unique_together = ['project', 'category']

    def __str__(self):
        return f'{self.project} - {self.category} ({self.is_enabled and "启用" or "禁用"})'


class RevenueShareConfig(models.Model):
    """项目分成配置（每个项目独立配置）"""
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name='share_config', verbose_name='项目'
    )
    share_ratio = models.DecimalField('分成比例', max_digits=5, decimal_places=4, default=0.50,
        help_text='如0.50表示合作方分50%')
    nurse_fee_rate = models.DecimalField('护士服务费比例', max_digits=5, decimal_places=4, default=0.10,
        help_text='护士服务费 = 收入 × 此比例（仅在勾选"护士服务费"科目时生效）')
    deductible_categories = models.ManyToManyField(
        CostCategory, blank=True, related_name='share_configs',
        verbose_name='可扣除费用科目', help_text='勾选哪些科目在分成前扣除（护士服务费不扣实际成本，而是 收入×比例）'
    )
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'project_share_config'
        verbose_name = '项目分成配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        cats = ', '.join(self.deductible_categories.values_list('name', flat=True)[:3])
        return f'{self.project} 分成{self.share_ratio*100:.0f}%'

    def save_history(self):
        """保存历史快照"""
        keys = list(self.deductible_categories.values_list('name', flat=True))
        RevenueShareConfigHistory.objects.create(
            project=self.project,
            share_ratio=self.share_ratio,
            nurse_fee_rate=self.nurse_fee_rate,
            deductible_keys=keys,
        )


class RevenueShareConfigHistory(models.Model):
    """分成配置历史版本"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='share_history', verbose_name='项目')
    share_ratio = models.DecimalField('分成比例', max_digits=5, decimal_places=4)
    nurse_fee_rate = models.DecimalField('护士服务费比例', max_digits=5, decimal_places=4)
    deductible_keys = models.JSONField('可扣除科目', default=list)
    changed_at = models.DateTimeField('修改时间', auto_now_add=True)

    class Meta:
        db_table = 'project_share_config_history'
        verbose_name = '配置历史'
        verbose_name_plural = verbose_name
        ordering = ['-changed_at']

    def __str__(self):
        return f'{self.project} {self.changed_at:%Y-%m-%d %H:%M}'


# ==================== 手工费用录入 ====================

class ManualCostEntry(models.Model):
    """手工录入的无账单来源费用（差旅费、接待费、杂费等）"""
    project = models.ForeignKey(
        Project, on_delete=models.PROTECT, related_name='manual_costs', verbose_name='归属项目'
    )
    category = models.ForeignKey(
        CostCategory, on_delete=models.PROTECT, related_name='manual_costs', verbose_name='费用科目'
    )
    amount = models.DecimalField('金额', max_digits=12, decimal_places=2)
    cost_date = models.DateField('发生日期')
    notes = models.TextField('备注说明', blank=True)
    created_at = models.DateTimeField('录入时间', auto_now_add=True)

    class Meta:
        db_table = 'project_manual_cost'
        verbose_name = '手工费用'
        verbose_name_plural = verbose_name
        ordering = ['-cost_date']

    def __str__(self):
        return f'{self.project} - {self.category}: {self.amount:,.0f}'


# ==================== 月度报表（自动汇总） ====================

class MonthlyReport(models.Model):
    """每个项目每月自动汇总的收入/费用/分成报表"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='monthly_reports', verbose_name='项目')
    year = models.IntegerField('年份')
    month = models.IntegerField('月份')

    # 收入
    payment_income = models.DecimalField('前台收款收入', max_digits=15, decimal_places=2, default=0)
    total_income = models.DecimalField('收入合计', max_digits=15, decimal_places=2, default=0)

    # 费用明细（按科目，存储JSON）
    cost_details = models.JSONField('费用明细', default=dict, blank=True,
        help_text='{"血检": 5000, "打针": 1200, "补剂": 800, ...}')
    total_cost = models.DecimalField('费用合计', max_digits=15, decimal_places=2, default=0)

    # 毛利与分成
    gross_profit = models.DecimalField('毛利', max_digits=15, decimal_places=2, default=0)
    service_fee = models.DecimalField('服务费扣除', max_digits=15, decimal_places=2, default=0,
        help_text='收入 × 服务费扣除比例')
    deductible_cost = models.DecimalField('可扣除费用合计', max_digits=15, decimal_places=2, default=0,
        help_text='仅计入配置中勾选的科目')
    share_base = models.DecimalField('分成基数', max_digits=15, decimal_places=2, default=0,
        help_text='收入 - 服务费 - 可扣除费用')
    share_amount = models.DecimalField('应付分成', max_digits=15, decimal_places=2, default=0)

    calculated_at = models.DateTimeField('计算时间', auto_now=True)

    class Meta:
        db_table = 'project_monthly_report'
        verbose_name = '月度报表'
        verbose_name_plural = verbose_name
        unique_together = ['project', 'year', 'month']
        ordering = ['-year', '-month', 'project']

    def __str__(self):
        return f'{self.project} {self.year}-{self.month:02d}: 收入{self.total_income:,.0f} 毛利{self.gross_profit:,.0f}'


def calculate_monthly_report(project, year, month):
    """计算指定项目指定月份的报表"""
    from apps.frontdesk.models import PaymentRecord
    from apps.inventory.models import StockOut
    from apps.lab_bills.models import LabBillRecord

    report, _ = MonthlyReport.objects.get_or_create(
        project=project, year=year, month=month
    )

    # 1. 前台收款收入
    payments = PaymentRecord.objects.filter(
        project=project, payment_date__year=year, payment_date__month=month
    )
    payment_income = payments.aggregate(s=Sum('amount'))['s'] or Decimal('0')

    # 2. 费用明细初始化
    cost_details = {}
    total_cost = Decimal('0')

    # 2a. 实验室血检费用
    lab_records = LabBillRecord.objects.filter(
        project=project, test_date__year=year, test_date__month=month
    )
    lab_cost = lab_records.aggregate(s=Sum('settlement_price'))['s'] or Decimal('0')
    if lab_cost:
        cost_details['血检'] = float(lab_cost)
        total_cost += lab_cost

    # 2b. 库存出库费用（按科目汇总）
    stock_outs = StockOut.objects.filter(
        project=project, created_at__year=year, created_at__month=month
    ).select_related('cost_category')
    for so in stock_outs:
        cat_name = so.cost_category.name if so.cost_category else '其他'
        cost_details[cat_name] = cost_details.get(cat_name, 0) + float(so.total_amount)
        total_cost += so.total_amount

    # 2c. 手工费用（按科目汇总）
    manual_entries = ManualCostEntry.objects.filter(
        project=project, cost_date__year=year, cost_date__month=month
    ).select_related('category')
    for me in manual_entries:
        cat_name = me.category.name
        cost_details[cat_name] = cost_details.get(cat_name, 0) + float(me.amount)
        total_cost += me.amount

    # 3. 计算毛利
    total_income = payment_income
    gross_profit = total_income - total_cost

    # 4. 计算分成（新公式）
    try:
        config = project.share_config
        deductible_names = set(config.deductible_categories.values_list('name', flat=True))
        # 护士服务费 = 收入 × 比例（仅当勾选"护士服务费"科目时）
        if '护士服务费' in deductible_names:
            service_fee = total_income * config.nurse_fee_rate
        else:
            service_fee = Decimal('0')
        # 可扣除费用 = 勾选科目的实际费用（排除护士服务费，它已经按比例计算）
        deductible_cost = Decimal('0')
        for cat_name, cat_amount in cost_details.items():
            if cat_name in deductible_names and cat_name != '护士服务费':
                deductible_cost += Decimal(str(cat_amount))
        # 分成基数 = 收入 - 护士服务费 - 其他可扣除费用
        share_base = total_income - service_fee - deductible_cost
        share_amount = share_base * config.share_ratio if share_base > 0 else Decimal('0')
    except Exception:
        service_fee = Decimal('0')
        deductible_cost = Decimal('0')
        share_base = Decimal('0')
        share_amount = Decimal('0')

    report.payment_income = payment_income
    report.total_income = total_income
    report.cost_details = cost_details
    report.total_cost = total_cost
    report.gross_profit = gross_profit
    report.service_fee = service_fee
    report.deductible_cost = deductible_cost
    report.share_base = share_base
    report.share_amount = share_amount
    report.save()

    return report
