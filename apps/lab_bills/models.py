"""
Module 2: Laboratory Bill Management (实验室账单管理)
Import bills from partner labs, add custom tags, filter and query.
"""
from django.db import models
from apps.core.models import UserStampedModel


class LabPartner(models.Model):
    """合作实验室"""
    name = models.CharField('实验室名称', max_length=100, unique=True)
    short_name = models.CharField('简称', max_length=50, blank=True)
    contact_person = models.CharField('联系人', max_length=50, blank=True)
    contact_phone = models.CharField('联系电话', max_length=30, blank=True)
    notes = models.TextField('备注', blank=True)
    is_active = models.BooleanField('启用', default=True)

    class Meta:
        db_table = 'lab_bills_partner'
        verbose_name = '合作实验室'
        verbose_name_plural = verbose_name
        ordering = ['name']

    def __str__(self):
        return self.short_name or self.name


class LabBillRecord(UserStampedModel):
    """实验室账单记录 - 从实验室账单取数后手动打标签的记录本"""
    # --- From bill import ---
    lab_partner = models.ForeignKey(
        LabPartner, on_delete=models.PROTECT, related_name='bill_records',
        verbose_name='合作方'
    )
    customer_name = models.CharField('客户姓名', max_length=100, db_index=True)
    test_date = models.DateField('检测日期', null=True, blank=True, db_index=True)
    test_package = models.CharField('检测项目/套餐', max_length=255, blank=True)
    package_code = models.CharField('套餐编码', max_length=100, blank=True)
    test_quantity = models.IntegerField('检测数量', default=1)
    standard_price = models.DecimalField('标准单价', max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField('折扣', max_digits=5, decimal_places=2, default=0,
        help_text='如 0.8 表示8折')
    settlement_price = models.DecimalField('实际结算价(折后)', max_digits=12, decimal_places=2, default=0,
        help_text='折后价格，直接取自实验室账单')

    # --- Custom tags (手动编辑) ---
    PAYER_CHOICES = [
        ('personal', '个人'),
        ('taikang', '泰康'),
        ('msh', 'MSH'),
        ('pingan', '平安'),
        ('hongkong', '香港'),
        ('union', '平台工会'),
    ]
    DEPARTMENT_CHOICES = [
        ('health_mgmt', '健康管理'),
        ('daily_med', '日常医疗'),
    ]
    PROJECT_CHOICES = [
        ('anti_aging', '抗衰老'),
        ('anti_aging_first', '抗衰老首次血检'),
        ('lifestyle', '生活方式门诊'),
        ('lifestyle_first', '生活方式门诊首次血检'),
        ('hormone', '荷尔蒙'),
        ('hormone_first', '荷尔蒙首次血检'),
        ('gut_flora', '肠道菌群'),
        ('alzheimers', '阿尔兹海默症'),
        ('glucose', '血糖代谢检测'),
        ('routine', '其他常规门诊'),
    ]

    payer = models.CharField('付款人', max_length=20, choices=PAYER_CHOICES, blank=True, db_index=True)
    department = models.CharField('科室', max_length=20, choices=DEPARTMENT_CHOICES, blank=True, db_index=True)
    project = models.CharField('项目', max_length=30, choices=PROJECT_CHOICES, blank=True, db_index=True)

    # --- Custom fields (1-2 reserved) ---
    custom_field_1 = models.CharField('自定义字段1', max_length=255, blank=True)
    custom_field_2 = models.CharField('自定义字段2', max_length=255, blank=True)

    # --- Meta ---
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('录入时间', auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'lab_bills_record'
        verbose_name = '实验室账单记录'
        verbose_name_plural = verbose_name
        ordering = ['-test_date', '-created_at']
        indexes = [
            models.Index(fields=['lab_partner', 'test_date']),
            models.Index(fields=['customer_name']),
            models.Index(fields=['payer', 'project']),
        ]

    def __str__(self):
        return f'{self.lab_partner.short_name} - {self.customer_name} - {self.test_package}'

    @classmethod
    def get_filter_summary(cls, queryset):
        """Calculate totals for filtered queryset."""
        agg = queryset.aggregate(
            total_qty=models.Sum('test_quantity'),
            total_amount=models.Sum('settlement_price')
        )
        return {
            'total_count': queryset.count(),
            'total_quantity': agg['total_qty'] or 0,
            'total_amount': agg['total_amount'] or 0,
        }


class LabBillImportLog(models.Model):
    """Bill import log for tracking file uploads."""
    lab_partner = models.ForeignKey(LabPartner, on_delete=models.CASCADE, verbose_name='合作方')
    file_name = models.CharField('文件名', max_length=255)
    records_imported = models.IntegerField('导入记录数', default=0)
    records_skipped = models.IntegerField('跳过记录数', default=0)
    errors = models.TextField('错误信息', blank=True)
    imported_at = models.DateTimeField('导入时间', auto_now_add=True)

    class Meta:
        db_table = 'lab_bills_import_log'
        verbose_name = '导入日志'
        verbose_name_plural = verbose_name
        ordering = ['-imported_at']

    def __str__(self):
        return f'{self.lab_partner.name} - {self.file_name} ({self.imported_at:%Y-%m-%d %H:%M})'
