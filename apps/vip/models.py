"""
Module 3: VIP Member Management (功能医学会员管理)
Treatment courses, payments, cost allocation, revenue recognition.
"""
from django.db import models
from apps.core.models import UserStampedModel


class VIPMember(UserStampedModel):
    """VIP member profile."""
    name = models.CharField('姓名', max_length=100, db_index=True)
    gender = models.CharField('性别', max_length=10, choices=[('M', '男'), ('F', '女')], default='M')
    phone = models.CharField('电话', max_length=30, blank=True)
    birth_date = models.DateField('出生日期', null=True, blank=True)
    id_number = models.CharField('证件号', max_length=50, blank=True)
    address = models.TextField('地址', blank=True)
    notes = models.TextField('备注', blank=True)
    is_active = models.BooleanField('活跃', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'vip_member'
        verbose_name = 'VIP会员'
        verbose_name_plural = verbose_name
        ordering = ['name']

    def __str__(self):
        return self.name


class VIPCourse(models.Model):
    """Treatment course for VIP member (疗程)."""
    DURATION_CHOICES = [
        (3, '3个月'),
        (6, '6个月'),
        (12, '12个月'),
    ]

    member = models.ForeignKey(VIPMember, on_delete=models.CASCADE, related_name='courses', verbose_name='会员')
    duration_months = models.IntegerField('疗程时长(月)', choices=DURATION_CHOICES)
    total_price = models.DecimalField('疗程总价', max_digits=12, decimal_places=2,
        help_text='范围: 30,000 - 250,000')
    start_date = models.DateField('开始日期')
    end_date = models.DateField('结束日期', null=True, blank=True)
    attending_doctor = models.CharField('合作医生', max_length=100, blank=True)
    status = models.CharField('状态', max_length=20, default='active',
        choices=[('active', '进行中'), ('completed', '已完成'), ('paused', '已暂停')])
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'vip_course'
        verbose_name = '疗程'
        verbose_name_plural = verbose_name
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.member.name} - {self.get_duration_months_display()} ({self.total_price:,.0f})'

    def save(self, *args, **kwargs):
        if self.start_date and not self.end_date:
            from dateutil.relativedelta import relativedelta
            self.end_date = self.start_date + relativedelta(months=self.duration_months) - relativedelta(days=1)
        super().save(*args, **kwargs)

    @property
    def monthly_revenue(self):
        """Monthly recognized revenue."""
        if self.duration_months and self.total_price:
            return self.total_price / self.duration_months
        return 0


class VIPPayment(UserStampedModel):
    """VIP payment record (收款记录)."""
    member = models.ForeignKey(VIPMember, on_delete=models.CASCADE, related_name='payments', verbose_name='会员')
    course = models.ForeignKey(VIPCourse, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='payments', verbose_name='关联疗程')
    amount = models.DecimalField('收款金额', max_digits=12, decimal_places=2)
    payment_date = models.DateField('收款日期', db_index=True)
    project_type = models.CharField('项目类型', max_length=100,
        help_text='如: 首次门诊、疗程费用、药费等')
    notes = models.TextField('备注', blank=True)

    class Meta:
        db_table = 'vip_payment'
        verbose_name = '收款记录'
        verbose_name_plural = verbose_name
        ordering = ['-payment_date']

    def __str__(self):
        return f'{self.member.name} {self.amount:,.0f} ({self.payment_date})'


class VIPCostItem(UserStampedModel):
    """VIP cost item for a course (疗程费用项)."""
    COST_TYPES = [
        ('first_visit', '首次门诊+血检'),
        ('injection', '点滴注射'),
        ('supplements', '餐包及营养补给'),
        ('blood_test', '血检'),
        ('imaging', '影像'),
        ('nurse_labor', '护士人工'),
        ('reception', '客户接待'),
        ('fixed_cost', '固定费用'),
        ('other', '其他自定义'),
    ]

    member = models.ForeignKey(VIPMember, on_delete=models.CASCADE, related_name='cost_items', verbose_name='会员')
    course = models.ForeignKey(VIPCourse, on_delete=models.CASCADE, related_name='cost_items', verbose_name='关联疗程')
    cost_type = models.CharField('费用类型', max_length=20, choices=COST_TYPES, db_index=True)
    custom_name = models.CharField('自定义名称', max_length=100, blank=True,
        help_text='仅"其他自定义"类型使用')

    # Amount fields
    standard_amount = models.DecimalField('标准金额', max_digits=12, decimal_places=2, default=0,
        help_text='标准/参考金额')
    cost_amount = models.DecimalField('成本金额', max_digits=12, decimal_places=2, default=0,
        help_text='实际成本金额')
    total_amount = models.DecimalField('总金额', max_digits=12, decimal_places=2, default=0,
        help_text='此项费用总金额')

    # For allocation: some costs are shared across courses
    is_per_course = models.BooleanField('按疗程均摊', default=False,
        help_text='固定费用类：总金额均分到每个疗程')

    # Links to other modules
    lab_bill_records = models.ManyToManyField(
        'lab_bills.LabBillRecord', blank=True, verbose_name='关联血检/影像账单'
    )
    stock_out_records = models.ManyToManyField(
        'inventory.StockOut', blank=True, verbose_name='关联保健品出库'
    )

    notes = models.TextField('备注', blank=True)
    cost_date = models.DateField('费用日期', null=True, blank=True)

    class Meta:
        db_table = 'vip_cost_item'
        verbose_name = '疗程费用项'
        verbose_name_plural = verbose_name
        ordering = ['member', 'course', 'cost_type']

    def __str__(self):
        name = self.custom_name or self.get_cost_type_display()
        return f'{self.member.name} - {name} ({self.total_amount:,.0f})'

    @property
    def allocated_amount(self):
        """Amount allocated per course if shared."""
        if self.is_per_course and self.total_amount:
            course_count = VIPCostItem.objects.filter(
                cost_type=self.cost_type, custom_name=self.custom_name
            ).exclude(is_per_course=False).values('course').distinct().count() or 1
            return self.total_amount / course_count
        return self.total_amount


class VIPRevenueRecognition(models.Model):
    """Monthly revenue recognition for VIP courses."""
    member = models.ForeignKey(VIPMember, on_delete=models.CASCADE, verbose_name='会员')
    course = models.ForeignKey(VIPCourse, on_delete=models.CASCADE, verbose_name='疗程')
    year = models.IntegerField('年份')
    month = models.IntegerField('月份')
    revenue_amount = models.DecimalField('确认收入', max_digits=12, decimal_places=2)
    is_confirmed = models.BooleanField('已确认', default=False)

    class Meta:
        db_table = 'vip_revenue_recognition'
        verbose_name = '收入确认'
        verbose_name_plural = verbose_name
        unique_together = ['course', 'year', 'month']
        ordering = ['year', 'month', 'member']

    def __str__(self):
        return f'{self.member.name} {self.year}-{self.month:02d}: {self.revenue_amount:,.0f}'
