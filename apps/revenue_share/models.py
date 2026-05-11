"""
Module 4: Revenue Share Management (合作机构分成管理)
Automatic revenue sharing calculation and reconciliation.
Partner institutions: 香港机构, 叶医生, 杨医生
"""
from django.db import models
from apps.core.models import UserStampedModel


class RevenuePartner(models.Model):
    """Partner institution for revenue sharing."""
    name = models.CharField('合作方名称', max_length=100, unique=True)
    project = models.CharField('关联项目', max_length=50,
        choices=[
            ('anti_aging', '抗衰老'),
            ('lifestyle', '生活方式门诊'),
            ('hormone', '荷尔蒙'),
        ]
    )
    contact_person = models.CharField('联系人', max_length=50, blank=True)
    contact_phone = models.CharField('联系电话', max_length=30, blank=True)
    notes = models.TextField('备注', blank=True)
    is_active = models.BooleanField('启用', default=True)

    class Meta:
        db_table = 'revenue_share_partner'
        verbose_name = '分成合作方'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.name} ({self.get_project_display()})'


class RevenueShareConfig(models.Model):
    """Revenue sharing configuration per partner."""
    partner = models.OneToOneField(
        RevenuePartner, on_delete=models.CASCADE,
        related_name='share_config', verbose_name='合作方'
    )
    # Deduction rate for nurse/reception costs (扣除护士/接待费比例)
    deduction_rate = models.DecimalField(
        '护士/接待费扣除比例', max_digits=5, decimal_places=4,
        default=0.10, help_text='如 0.10 表示扣除10%'
    )
    # Split ratio after deductions (分成比例)
    partner_share_ratio = models.DecimalField(
        '合作方分成比例', max_digits=5, decimal_places=4,
        default=0.50, help_text='如 0.50 表示50%'
    )
    # Deductible cost items (可扣除的费用项)
    deduct_lab_bills = models.BooleanField('扣除实验室费用', default=True)
    deduct_supplements = models.BooleanField('扣除保健品费用', default=True)
    deduct_imaging = models.BooleanField('扣除影像费用', default=True)
    deduct_nurse = models.BooleanField('扣除护士人工', default=True)
    deduct_reception = models.BooleanField('扣除客户接待', default=True)
    deduct_travel = models.BooleanField('扣除差旅费', default=True)
    deduct_fixed = models.BooleanField('扣除固定费用', default=True)

    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'revenue_share_config'
        verbose_name = '分成配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.partner.name} 配置 (扣除{self.deduction_rate*100:.0f}%, 分成{self.partner_share_ratio*100:.0f}%)'


class RevenueShareCalculation(models.Model):
    """Monthly revenue share calculation for a partner."""
    partner = models.ForeignKey(
        RevenuePartner, on_delete=models.CASCADE, related_name='calculations', verbose_name='合作方'
    )
    year = models.IntegerField('年份')
    month = models.IntegerField('月份')

    # Input values
    total_course_revenue = models.DecimalField('疗程总收入', max_digits=15, decimal_places=2, default=0)
    nurse_reception_deduction = models.DecimalField('扣除护士/接待费', max_digits=15, decimal_places=2, default=0)
    total_deductions = models.DecimalField('总扣除额', max_digits=15, decimal_places=2, default=0)

    # Result
    net_revenue = models.DecimalField('净收入(分成前)', max_digits=15, decimal_places=2, default=0)
    partner_share = models.DecimalField('应付分成', max_digits=15, decimal_places=2, default=0)

    # Status
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('confirmed', '已确认'),
        ('settled', '已结算'),
    ]
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField('备注', blank=True)
    calculated_at = models.DateTimeField('计算时间', auto_now_add=True)

    class Meta:
        db_table = 'revenue_share_calculation'
        verbose_name = '分成计算'
        verbose_name_plural = verbose_name
        unique_together = ['partner', 'year', 'month']
        ordering = ['-year', '-month', 'partner']

    def __str__(self):
        return f'{self.partner.name} {self.year}-{self.month:02d}: {self.partner_share:,.0f}'


class ReconciliationStatement(models.Model):
    """Monthly reconciliation statement (对账单)."""
    partner = models.ForeignKey(RevenuePartner, on_delete=models.CASCADE, verbose_name='合作方')
    year = models.IntegerField('年份')
    month = models.IntegerField('月份')
    calculation = models.OneToOneField(
        RevenueShareCalculation, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='关联分成计算'
    )
    statement_data = models.JSONField('对账明细', default=dict, blank=True)
    total_amount = models.DecimalField('对账总金额', max_digits=15, decimal_places=2, default=0)
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('sent', '已发送'),
        ('confirmed', '已确认'),
    ]
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='draft')
    generated_at = models.DateTimeField('生成时间', auto_now_add=True)
    confirmed_at = models.DateTimeField('确认时间', null=True, blank=True)
    notes = models.TextField('备注', blank=True)

    class Meta:
        db_table = 'revenue_share_statement'
        verbose_name = '对账单'
        verbose_name_plural = verbose_name
        unique_together = ['partner', 'year', 'month']
        ordering = ['-year', '-month']

    def __str__(self):
        return f'{self.partner.name} {self.year}-{self.month:02d} 对账单'
