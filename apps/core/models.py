"""
Core shared models for the clinic management system.
Includes: CustomField system, base abstract models, system settings.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""
    created_at = models.DateTimeField('创建时间', default=timezone.now, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        abstract = True


class UserStampedModel(TimeStampedModel):
    """Abstract model with user tracking."""
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name='创建人'
    )
    updated_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name='更新人'
    )

    class Meta:
        abstract = True


class CustomFieldDefinition(models.Model):
    """Allows users to add custom fields to entity types."""
    FIELD_TYPES = [
        ('text', '文本'),
        ('number', '数字'),
        ('date', '日期'),
        ('boolean', '是/否'),
        ('select', '下拉选择'),
    ]

    name = models.CharField('字段名称', max_length=100)
    field_type = models.CharField('字段类型', max_length=20, choices=FIELD_TYPES, default='text')
    entity_type = models.CharField('关联实体', max_length=100, db_index=True,
        help_text='如: customer, lab_bill, expense 等')
    options = models.TextField('下拉选项', blank=True,
        help_text='仅下拉类型使用，每行一个选项')
    is_required = models.BooleanField('必填', default=False)
    order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'core_custom_field_def'
        verbose_name = '自定义字段定义'
        verbose_name_plural = verbose_name
        ordering = ['entity_type', 'order']

    def __str__(self):
        return f'{self.entity_type} - {self.name}'

    def get_options_list(self):
        return [o.strip() for o in self.options.split('\n') if o.strip()]


class CustomFieldValue(models.Model):
    """Stores custom field values for specific entity instances."""
    definition = models.ForeignKey(
        CustomFieldDefinition, on_delete=models.CASCADE,
        related_name='values', verbose_name='字段定义'
    )
    entity_id = models.PositiveIntegerField('实体ID')
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, verbose_name='实体类型'
    )
    entity = GenericForeignKey('content_type', 'entity_id')
    value_text = models.TextField('文本值', blank=True, default='')
    value_number = models.DecimalField('数字值', max_digits=15, decimal_places=2, null=True, blank=True)
    value_date = models.DateField('日期值', null=True, blank=True)
    value_boolean = models.BooleanField('布尔值', default=False)

    class Meta:
        db_table = 'core_custom_field_val'
        verbose_name = '自定义字段值'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['content_type', 'entity_id']),
        ]
        unique_together = ['definition', 'content_type', 'entity_id']

    @property
    def display_value(self):
        if self.definition.field_type == 'number' and self.value_number is not None:
            return str(self.value_number)
        elif self.definition.field_type == 'date' and self.value_date:
            return self.value_date.strftime('%Y-%m-%d')
        elif self.definition.field_type == 'boolean':
            return '是' if self.value_boolean else '否'
        return self.value_text

    def set_value(self, value):
        ft = self.definition.field_type
        if ft == 'text' or ft == 'select':
            self.value_text = str(value) if value else ''
        elif ft == 'number':
            self.value_number = value
        elif ft == 'date':
            self.value_date = value
        elif ft == 'boolean':
            self.value_boolean = bool(value)


class SystemConfig(models.Model):
    """Key-value system configuration storage."""
    key = models.CharField('配置键', max_length=100, unique=True)
    value = models.TextField('配置值', blank=True)
    description = models.CharField('说明', max_length=255, blank=True)
    config_type = models.CharField('类型', max_length=20, default='text',
        choices=[('text', '文本'), ('number', '数字'), ('json', 'JSON'), ('boolean', '布尔')])
    category = models.CharField('分类', max_length=50, default='general')
    updated_at = models.DateTimeField('修改时间', auto_now=True)

    class Meta:
        db_table = 'core_system_config'
        verbose_name = '系统配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.key}: {self.value[:50]}'

    @classmethod
    def get(cls, key, default=None):
        try:
            obj = cls.objects.get(key=key)
            if obj.config_type == 'number':
                try:
                    return float(obj.value)
                except ValueError:
                    return obj.value
            elif obj.config_type == 'json':
                import json
                return json.loads(obj.value)
            elif obj.config_type == 'boolean':
                return obj.value.lower() in ('true', '1', 'yes')
            return obj.value
        except cls.DoesNotExist:
            return default
