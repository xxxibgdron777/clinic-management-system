"""
Role-based access control - extended user profile.
Roles: 管理员(admin), 前台(frontdesk), 库房(warehouse), 合作方(partner)
"""
from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel


class UserProfile(models.Model):
    """Extended user profile with role and contact info."""
    ROLE_ADMIN = 'admin'
    ROLE_FRONTDESK = 'frontdesk'
    ROLE_WAREHOUSE = 'warehouse'
    ROLE_PARTNER = 'partner'

    ROLE_CHOICES = [
        (ROLE_ADMIN, '管理员'),
        (ROLE_FRONTDESK, '前台'),
        (ROLE_WAREHOUSE, '库房'),
        (ROLE_PARTNER, '合作方'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='用户')
    role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, default=ROLE_FRONTDESK)
    phone = models.CharField('电话', max_length=20, blank=True)
    department = models.CharField('部门', max_length=50, blank=True)
    notes = models.TextField('备注', blank=True)

    class Meta:
        db_table = 'accounts_user_profile'
        verbose_name = '用户档案'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_frontdesk(self):
        return self.role == self.ROLE_FRONTDESK

    @property
    def is_warehouse(self):
        return self.role == self.ROLE_WAREHOUSE

    @property
    def is_partner(self):
        return self.role == self.ROLE_PARTNER

    @classmethod
    def get_accessible_modules(cls, role):
        """Return list of module names accessible by role."""
        perms = {
            cls.ROLE_ADMIN: ['inventory', 'lab_bills', 'vip', 'revenue_share',
                              'billing', 'reports', 'frontdesk', 'accounts', 'admin'],
            cls.ROLE_FRONTDESK: ['inventory', 'lab_bills', 'vip', 'frontdesk', 'reports'],
            cls.ROLE_WAREHOUSE: ['inventory', 'lab_bills'],
            cls.ROLE_PARTNER: ['revenue_share', 'billing', 'reports'],
        }
        return perms.get(role, [])
