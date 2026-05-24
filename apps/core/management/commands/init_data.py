"""
Management command to initialize essential reference data:
- Lab partners (合作实验室)
- Revenue partners (分成合作方)
- Report categories (报表分类)
- Admin user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.lab_bills.models import LabPartner
from apps.revenue_share.models import RevenuePartner, RevenueShareConfig
from apps.reports.models import ReportCategory, ReportItem
from apps.accounts_app.models import UserProfile


class Command(BaseCommand):
    help = '初始化基础数据'

    def handle(self, *args, **options):
        self._create_superuser()
        self._create_lab_partners()
        self._create_revenue_partners()
        self._create_report_categories()
        self.stdout.write(self.style.SUCCESS('基础数据初始化完成!'))

    def _create_superuser(self):
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser('admin', 'admin@clinic.com', 'admin123')
            UserProfile.objects.get_or_create(user=user, defaults={
                'role': UserProfile.ROLE_ADMIN, 'phone': ''
            })
            self.stdout.write('  创建管理员: admin / admin123')

    def _create_lab_partners(self):
        labs = [
            ('华测检测', '华测', '', ''),
            ('迪恩诊断', '迪恩', '', ''),
            ('华莱士医学', '华莱士', '', ''),
            ('鼎坤科技', '鼎坤', '', ''),
            ('博厚健康', '博厚', '', ''),
        ]
        for name, short, contact, phone in labs:
            LabPartner.objects.get_or_create(name=name, defaults={
                'short_name': short, 'contact_person': contact, 'contact_phone': phone
            })
        self.stdout.write(f'  合作实验室: {LabPartner.objects.count()} 家')

    def _create_revenue_partners(self):
        partners = [
            ('香港机构', 'anti_aging', '香港抗衰老', ''),
            ('叶医生', 'lifestyle', '生活方式门诊', ''),
            ('杨医生', 'hormone', '荷尔蒙项目', ''),
        ]
        for name, project, contact, phone in partners:
            partner, created = RevenuePartner.objects.get_or_create(
                name=name, defaults={'project': project, 'contact_person': contact, 'contact_phone': phone}
            )
            # Default config: 10% deduction, 50% share for Ye/Yang; customizable for HK
            if created:
                share_ratio = 0.50
                RevenueShareConfig.objects.create(partner=partner, deduction_rate=0.10, partner_share_ratio=share_ratio)
        self.stdout.write(f'  分成合作方: {RevenuePartner.objects.count()} 家')

    def _create_report_categories(self):
        categories = [
            ('业务对象', 1, False, ['打针', '输液', '采血', '心电图', '其他治疗']),
            ('功能医学/健康管理', 2, False, [
                '阿尔茨海默症检测', '肠道菌群检测', '血糖代谢检测',
                '抗衰老项目', '荷尔蒙项目', '生活方式门诊',
                '糖尿病管理', '心血管检测',
            ]),
            # ('神经康复', 3, True, ['神经评估', '认知训练', '言语治疗', '作业治疗']),  # 暂时移除
        ]
        for name, order, editable, items in categories:
            cat, _ = ReportCategory.objects.get_or_create(
                name=name, defaults={'order': order, 'is_editable': editable, 'is_active': True}
            )
            for i, item_name in enumerate(items):
                ReportItem.objects.get_or_create(
                    category=cat, name=item_name,
                    defaults={'order': i, 'is_active': True}
                )
        self.stdout.write(f'  报表分类: {ReportCategory.objects.count()} 个, 项目: {ReportItem.objects.count()} 个')
