"""
Module 7: Front Desk Operations (前台日常操作)
Daily payment tracking from payment platforms (通联支付).
"""
from django.db import models
from apps.core.models import UserStampedModel


class PaymentRecord(models.Model):
    """Payment record imported from payment gateway or manually entered."""
    PAYMENT_TYPES = [
        ('outpatient', '门诊'),
        ('lab', '检测'),
        ('medication', '药费'),
        ('injection', '打针/输液'),
        ('supplements', '保健品'),
        ('other', '其他'),
    ]

    PAYER_TYPES = [
        ('self', '自费'),
        ('pingan', '平安保险'),
        ('msh', 'MSH保险'),
        ('taikang', '泰康保险'),
        ('corporate', '企业合作'),
    ]

    customer_name = models.CharField('客户姓名', max_length=100, db_index=True)
    vip_member = models.ForeignKey(
        'vip.VIPMember', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='frontdesk_payments', verbose_name='关联会员'
    )
    payment_date = models.DateField('收款日期', db_index=True)
    amount = models.DecimalField('金额', max_digits=12, decimal_places=2)
    description = models.CharField('收费项目描述', max_length=200, blank=True)
    project = models.ForeignKey(
        'projects.Project', on_delete=models.PROTECT, null=True, blank=True,
        related_name='payments', verbose_name='归属项目',
        help_text='必选：6个合作项目之一，系统自动按项目汇总每月收入'
    )
    payment_type = models.CharField('收费类型', max_length=20, choices=PAYMENT_TYPES, default='outpatient')
    payer_type = models.CharField('收入类型', max_length=20, choices=PAYER_TYPES, default='self',
        help_text='付款方类型：自费/保险/企业')
    # Reference info from payment platform
    transaction_ref = models.CharField('交易流水号', max_length=100, blank=True,
        help_text='通联支付流水号')
    source_file = models.CharField('来源文件', max_length=255, blank=True)

    # Insurance claim tracking (后续扩展)
    insurance_claimed = models.BooleanField('已申请理赔', default=False)
    insurance_claim_date = models.DateField('理赔日期', null=True, blank=True)
    insurance_status = models.CharField('理赔状态', max_length=20, blank=True)

    # Invoice management (后续扩展)
    invoiced = models.BooleanField('已开票', default=False)
    invoice_number = models.CharField('发票号', max_length=50, blank=True)

    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('录入时间', auto_now_add=True)

    class Meta:
        db_table = 'frontdesk_payment'
        verbose_name = '收款记录'
        verbose_name_plural = verbose_name
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f'{self.customer_name} {self.amount:,.0f} ({self.payment_date})'


class CashRecord(models.Model):
    """Cash management record."""
    TYPE_CHOICES = [
        ('income', '收款'),
        ('expense', '支出'),
        ('reimburse', '报销'),
    ]
    record_date = models.DateField('日期')
    type = models.CharField('类型', max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField('金额', max_digits=12, decimal_places=2)
    description = models.CharField('说明', max_length=255)
    payee = models.CharField('收款/付款人', max_length=100, blank=True)
    category = models.CharField('费用类别', max_length=50, blank=True)
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'frontdesk_cash'
        verbose_name = '现金记录'
        verbose_name_plural = verbose_name
        ordering = ['-record_date']

    def __str__(self):
        return f'{self.get_type_display()}: {self.amount:,.0f} ({self.record_date})'
