"""
Module 1: Inventory Management (保健品/补剂/耗材库存管理)
Products, Stock In, Stock Out with project linkage.
"""
from decimal import Decimal
from django.db import models
from apps.core.models import UserStampedModel

CATEGORY_CHOICES = [
    ('injection', '打针类'),
    ('supplement', '补剂类'),
    ('other', '其他'),
]


class Product(models.Model):
    """Product with category-based cost mapping."""
    name_cn = models.CharField('中文名称', max_length=200)
    name_en = models.CharField('英文名称', max_length=200, blank=True)
    category = models.CharField('类别', max_length=20, choices=CATEGORY_CHOICES, default='supplement')
    unit = models.CharField('最小单位', max_length=20, default='瓶',
        help_text='如：瓶、盒、粒')
    cost_price = models.DecimalField('成本单价', max_digits=12, decimal_places=2)
    selling_price = models.DecimalField('销售单价', max_digits=12, decimal_places=2, default=0,
        help_text='默认 = 成本价 × 130%')
    expiry_date = models.DateField('有效期', null=True, blank=True)
    supplier = models.CharField('供应商/采购平台', max_length=200, blank=True)
    current_stock = models.IntegerField('当前库存数量', default=0)
    min_stock_threshold = models.IntegerField('库存预警阈值', default=10)
    batch_number = models.CharField('批次号', max_length=100, blank=True)
    barcode = models.CharField('条形码', max_length=100, blank=True)
    notes = models.TextField('备注', blank=True)
    is_active = models.BooleanField('启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'inventory_product'
        verbose_name = '商品'
        verbose_name_plural = verbose_name
        ordering = ['name_cn']
        indexes = [
            models.Index(fields=['name_cn']),
            models.Index(fields=['supplier']),
        ]

    def save(self, *args, **kwargs):
        # 销售单价默认 = 成本价 × 130%
        if not self.selling_price and self.cost_price:
            self.selling_price = self.cost_price * Decimal('1.3')
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.name_cn
        if self.name_en:
            name = f'{name} ({self.name_en})'
        return name

    @property
    def display_name(self):
        return str(self)

    @property
    def stock_status(self):
        if self.current_stock <= 0:
            return '缺货'
        if self.current_stock <= self.min_stock_threshold:
            return '低库存'
        return '正常'

    @property
    def cost_category_name(self):
        """根据类别映射到费用科目名"""
        mapping = {'injection': '打针', 'supplement': '补剂'}
        return mapping.get(self.category, '其他')


class StockIn(UserStampedModel):
    """Stock-in record (入库记录)."""
    STOCK_IN_TYPE_SALES = (('purchase', '采购入库'), ('return', '退货入库'), ('adjust', '盘点调整'))

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_ins', verbose_name='商品')
    quantity = models.IntegerField('入库数量')
    unit_price = models.DecimalField('单价', max_digits=12, decimal_places=2)
    total_amount = models.DecimalField('总金额', max_digits=12, decimal_places=2, editable=False)
    type = models.CharField('入库类型', max_length=20, choices=STOCK_IN_TYPE_SALES, default='purchase')
    supplier = models.CharField('供应商', max_length=200, blank=True)
    batch_number = models.CharField('批次号', max_length=100, blank=True)
    expiry_date = models.DateField('有效期', null=True, blank=True)
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('入库时间', auto_now_add=True)
    confirmed = models.BooleanField('已确认', default=False)

    class Meta:
        db_table = 'inventory_stock_in'
        verbose_name = '入库记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new and self.confirmed:
            self.product.current_stock += self.quantity
            self.product.save(update_fields=['current_stock', 'updated_at'])

    def __str__(self):
        return f'{self.product.name_cn} +{self.quantity} ({self.get_type_display()})'


class StockOut(UserStampedModel):
    """出库记录 - 必须关联客户和项目"""
    TYPE_SALE = 'sale'
    TYPE_SCRAP = 'scrap'
    OUT_TYPES = [
        (TYPE_SALE, '销售出库'),
        (TYPE_SCRAP, '报废出库'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_outs', verbose_name='商品')
    quantity = models.IntegerField('出库数量')
    unit_price = models.DecimalField('单价', max_digits=12, decimal_places=2)
    total_amount = models.DecimalField('总金额', max_digits=12, decimal_places=2, editable=False)
    out_type = models.CharField('出库类型', max_length=20, choices=OUT_TYPES, default=TYPE_SALE)
    customer_name = models.CharField('客户姓名', max_length=100, help_text='必填')
    vip_member = models.ForeignKey(
        'vip.VIPMember', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_outs', verbose_name='关联会员'
    )
    project = models.ForeignKey(
        'projects.Project', on_delete=models.PROTECT, null=True, blank=True,
        related_name='stock_outs', verbose_name='归属项目'
    )
    cost_category = models.ForeignKey(
        'projects.CostCategory', on_delete=models.PROTECT, null=True, blank=True,
        related_name='stock_outs', verbose_name='费用科目',
        help_text='根据物品类别自动映射：打针类→打针，补剂类→补剂'
    )
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('出库时间', auto_now_add=True)

    class Meta:
        db_table = 'inventory_stock_out'
        verbose_name = '出库记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        # 自动根据物品类别映射费用科目
        if not self.cost_category_id and self.product:
            try:
                cat_name = self.product.cost_category_name
                cat = __import__('apps.projects.models', fromlist=['CostCategory']).CostCategory.objects.filter(name=cat_name).first()
                if cat:
                    self.cost_category = cat
            except Exception:
                pass
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new:
            self.product.current_stock -= self.quantity
            self.product.save(update_fields=['current_stock', 'updated_at'])

    def __str__(self):
        return f'{self.product.name_cn} -{self.quantity} ({self.get_out_type_display()})'
