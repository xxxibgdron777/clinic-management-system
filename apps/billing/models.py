"""
Module 5: Bill Generation (账单生成)
Import data from ABC medical system, generate bills for partner settlement.
"""
from django.db import models
from apps.core.models import UserStampedModel


class BillImport(models.Model):
    """Imported bill data from ABC medical system."""
    customer_name = models.CharField('客户姓名', max_length=100, db_index=True)
    bill_date = models.DateField('日期', db_index=True)
    item_name = models.CharField('名称', max_length=255)
    unit_price = models.DecimalField('单价', max_digits=12, decimal_places=2)
    quantity = models.IntegerField('数量', default=1)
    amount = models.DecimalField('金额', max_digits=12, decimal_places=2)
    hkd_amount = models.DecimalField('港币金额', max_digits=12, decimal_places=2, default=0)
    source_file = models.CharField('来源文件', max_length=255, blank=True)
    imported_at = models.DateTimeField('导入时间', auto_now_add=True)

    class Meta:
        db_table = 'billing_import'
        verbose_name = '导入账单明细'
        verbose_name_plural = verbose_name
        ordering = ['-bill_date']

    def __str__(self):
        return f'{self.customer_name} - {self.item_name} ({self.amount})'


class BillTemplate(models.Model):
    """Pre-defined bill template for partner settlement."""
    name = models.CharField('模板名称', max_length=100)
    description = models.TextField('模板说明', blank=True)
    partner_type = models.CharField('适用合作方', max_length=50, blank=True)
    fields_config = models.JSONField('字段配置', default=list,
        help_text='JSON array of field definitions')
    is_active = models.BooleanField('启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'billing_template'
        verbose_name = '账单模板'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GeneratedBill(models.Model):
    """Generated bill for a specific month and partner."""
    template = models.ForeignKey(BillTemplate, on_delete=models.SET_NULL, null=True, verbose_name='模板')
    partner_name = models.CharField('合作方', max_length=100)
    year = models.IntegerField('年份')
    month = models.IntegerField('月份')
    bill_data = models.JSONField('账单数据', default=dict)
    total_amount = models.DecimalField('总金额', max_digits=15, decimal_places=2, default=0)
    hkd_total = models.DecimalField('港币总金额', max_digits=15, decimal_places=2, default=0)
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('generated', '已生成'),
        ('sent', '已发送'),
    ]
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='draft')
    generated_at = models.DateTimeField('生成时间', auto_now_add=True)
    notes = models.TextField('备注', blank=True)

    class Meta:
        db_table = 'billing_generated'
        verbose_name = '已生成账单'
        verbose_name_plural = verbose_name
        ordering = ['-year', '-month']

    def __str__(self):
        return f'{self.partner_name} {self.year}-{self.month:02d} 账单'
