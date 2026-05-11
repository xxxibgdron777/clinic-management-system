"""
Module 6: Monthly Reports (每月报表)
Dynamic report items that users can add/edit, with monthly filtering and export.
"""
from django.db import models
from apps.core.models import UserStampedModel


class ReportCategory(models.Model):
    """Report category (业务对象 / 功能医学 / 运动康复 / 神经康复)."""
    name = models.CharField('分类名称', max_length=100, unique=True)
    order = models.IntegerField('排序', default=0)
    is_editable = models.BooleanField('可在线编辑', default=False,
        help_text='运动康复、神经康复等简单模块支持在线编辑')
    is_active = models.BooleanField('启用', default=True)

    class Meta:
        db_table = 'reports_category'
        verbose_name = '报表分类'
        verbose_name_plural = verbose_name
        ordering = ['order']

    def __str__(self):
        return self.name


class ReportItem(models.Model):
    """Individual report item that can be dynamically added."""
    category = models.ForeignKey(
        ReportCategory, on_delete=models.CASCADE,
        related_name='items', verbose_name='分类'
    )
    name = models.CharField('项目名称', max_length=200)
    description = models.TextField('说明', blank=True)
    unit_price = models.DecimalField('单价', max_digits=12, decimal_places=2, default=0)
    order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('启用', default=True)

    class Meta:
        db_table = 'reports_item'
        verbose_name = '报表项目'
        verbose_name_plural = verbose_name
        ordering = ['category', 'order']

    def __str__(self):
        return f'{self.category.name} - {self.name}'


class MonthlyReportEntry(models.Model):
    """Monthly report data entry."""
    report_item = models.ForeignKey(
        ReportItem, on_delete=models.CASCADE,
        related_name='monthly_entries', verbose_name='报表项目'
    )
    year = models.IntegerField('年份')
    month = models.IntegerField('月份')
    quantity = models.IntegerField('数量', default=0)
    amount = models.DecimalField('金额', max_digits=15, decimal_places=2, default=0)
    notes = models.TextField('备注', blank=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'reports_entry'
        verbose_name = '月度报表数据'
        verbose_name_plural = verbose_name
        unique_together = ['report_item', 'year', 'month']
        ordering = ['-year', '-month', 'report_item']

    def __str__(self):
        return f'{self.report_item.name} {self.year}-{self.month:02d}: {self.amount:,.0f}'
