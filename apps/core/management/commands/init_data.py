"""
Management command to initialize essential reference data:
- Admin user, Lab partners, Cost categories
- Partners (合作商) + Projects (15个)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.lab_bills.models import LabPartner
from apps.projects.models import Partner, Project, CostCategory, ProjectCategoryConfig, RevenueShareConfig
from apps.accounts_app.models import UserProfile


class Command(BaseCommand):
    help = '初始化基础数据'

    def handle(self, *args, **options):
        self._create_superuser()
        self._create_lab_partners()
        self._create_cost_categories()
        self._create_partners_and_projects()
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
            ('华测检测', '华测'), ('迪恩诊断', '迪恩'), ('华莱士医学', '华莱士'),
        ]
        for name, short in labs:
            LabPartner.objects.get_or_create(name=name, defaults={'short_name': short})
        self.stdout.write(f'  合作实验室: {LabPartner.objects.count()} 家')

    def _create_cost_categories(self):
        categories = [
            ('打针', '输液/注射', 1),
            ('补剂', '餐包/营养', 2),
            ('护士服务费', '', 3),
            ('影像检查', '', 4),
            ('中期血检', '', 5),
            ('客户接待费', '早餐、快递、打印等', 6),
            ('差旅费', '合作医生面诊差旅', 7),
            ('其他', '用户自定义科目', 99),
        ]
        for name, desc, order in categories:
            CostCategory.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'order': order, 'is_system': True, 'is_active': True}
            )
        self.stdout.write(f'  费用科目: {CostCategory.objects.count()} 个')

    def _create_partners_and_projects(self):
        """创建合作商及15个完整项目"""
        # 确保所有合作商存在
        partner_names = ['香港巴黎', '叶医生', '杨医生', '老干局', '平台工会', '其他']
        for pn in partner_names:
            Partner.objects.get_or_create(name=pn)

        # 完整项目表：合作商, 项目全称, 简称, 类型, 疗程月数
        all_projects = [
            # 香港巴黎
            ('香港巴黎', '香港巴黎 疗程管理',     '抗衰老',             'course_mgmt', 12),
            ('香港巴黎', '香港巴黎 首次血检',     '抗衰老首次血检',     'first_test',   1),
            # 叶医生
            ('叶医生',  '叶医生 疗程管理',        '生活方式门诊',       'course_mgmt', 12),
            ('叶医生',  '叶医生 首次血检',        '生活方式门诊首次血检','first_test',   1),
            # 杨医生
            ('杨医生',  '杨医生 疗程管理',        '荷尔蒙',             'course_mgmt', 12),
            ('杨医生',  '杨医生 首次血检',        '荷尔蒙首次血检',     'first_test',   1),
            # 其他
            ('其他',    '肠道菌群',               '肠道菌群',           'first_test',   1),
            ('其他',    '阿尔兹海默症',           '阿尔兹海默症',       'first_test',   1),
            ('其他',    '血糖代谢检测',           '血糖代谢检测',       'first_test',   1),
            ('其他',    '其他常规门诊',           '其他常规门诊',       'first_test',   1),
            # 老干局
            ('老干局',  '2026外交部体检',         '2026外交部体检',     'first_test',   1),
            ('老干局',  '2026商务部体检',         '2026商务部体检',     'first_test',   1),
            ('老干局',  '2025外交部体检',         '2025外交部体检',     'first_test',   1),
            # 平台工会
            ('平台工会','2026平台员工健康咨询',   '2026平台员工健康咨询','first_test',   1),
            ('平台工会','2025平台员工体检',       '2025平台员工体检',   'first_test',   1),
        ]

        for pname, proj_name, short_name, proj_type, duration in all_projects:
            partner = Partner.objects.get(name=pname)
            proj, _ = Project.objects.update_or_create(
                partner=partner, name=proj_name,
                defaults={
                    'project_type': proj_type,
                    'short_name': short_name,
                    'duration_months': duration,
                    'unit_price': 0,
                    'is_active': True,
                }
            )
            # 分成默认配置
            config, _ = RevenueShareConfig.objects.get_or_create(
                project=proj, defaults={'share_ratio': 0.50, 'nurse_fee_rate': 0.10}
            )
            if not config.deductible_categories.exists():
                config.deductible_categories.set(CostCategory.objects.filter(is_system=True))
            # 关联科目
            for cat in CostCategory.objects.filter(is_system=True):
                ProjectCategoryConfig.objects.get_or_create(
                    project=proj, category=cat, defaults={'is_enabled': True}
                )

        self.stdout.write(f'  合作商: {Partner.objects.count()} 家')
        self.stdout.write(f'  合作项目: {Project.objects.count()} 个')
        self.stdout.write(f'  分成配置: {RevenueShareConfig.objects.count()} 个')
