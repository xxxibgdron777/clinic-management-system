"""
Management command to initialize essential reference data:
- Admin user
- Lab partners
- Partners (合作商) + Projects (6个项目)
- Cost categories (统一费用科目库)
- Revenue share configs
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
        """创建统一费用科目库"""
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
        """创建3个合作商及其6个项目"""
        partners_config = [
            ('香港巴黎', '抗衰老', [
                ('香港巴黎 首次血检', 'first_test', 0, 1),
                ('香港巴黎 疗程管理', 'course_mgmt', 0, 12),
            ]),
            ('叶医生', '生活方式门诊', [
                ('叶医生 首次血检', 'first_test', 0, 1),
                ('叶医生 疗程管理', 'course_mgmt', 0, 12),
            ]),
            ('杨医生', '荷尔蒙门诊', [
                ('杨医生 首次血检', 'first_test', 0, 1),
                ('杨医生 疗程管理', 'course_mgmt', 0, 12),
            ]),
        ]
        for pname, pdesc, projects in partners_config:
            partner, created = Partner.objects.get_or_create(
                name=pname, defaults={'notes': pdesc}
            )

            for idx, (proj_name, proj_type, price, duration) in enumerate(projects):
                proj, _ = Project.objects.update_or_create(
                    partner=partner, name=proj_name,
                    defaults={
                        'project_type': proj_type,
                        'unit_price': price,
                        'duration_months': duration,
                        'order': idx,
                        'is_active': True,
                    }
                )
                # 每个项目默认分成配置
                config, _ = RevenueShareConfig.objects.get_or_create(
                    project=proj, defaults={'share_ratio': 0.50, 'nurse_fee_rate': 0.10}
                )
                if not config.deductible_categories.exists():
                    config.deductible_categories.set(CostCategory.objects.filter(is_system=True))
                # 自动关联所有系统科目
                for cat in CostCategory.objects.filter(is_system=True):
                    ProjectCategoryConfig.objects.get_or_create(
                        project=proj, category=cat, defaults={'is_enabled': True}
                    )

        self.stdout.write(f'  合作商: {Partner.objects.count()} 家')
        self.stdout.write(f'  合作项目: {Project.objects.count()} 个')
        self.stdout.write(f'  分成配置: {RevenueShareConfig.objects.count()} 个')
