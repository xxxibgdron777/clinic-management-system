# 综合性诊所管理系统

基于 Django 4.2 的 B/S 架构诊所管理系统，支持库存管理、实验室账单、VIP会员、合作分成、账单生成、报表等全方位业务。

## 技术栈

- **后端**: Python 3.10+ / Django 4.2 / PostgreSQL(推荐) 或 SQLite
- **前端**: Bootstrap 5.3 / Crispy Forms / 原生 JS
- **Excel**: openpyxl / xlrd / pandas
- **导入导出**: django-import-export

## 快速启动

### 1. 安装依赖

```bash
cd clinic_management
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python manage.py makemigrations core inventory lab_bills vip revenue_share billing reports frontdesk accounts_app
python manage.py migrate
```

### 3. 初始化基础数据

```bash
python manage.py init_data
```

创建管理员: `admin` / `admin123`
预置: 5家合作实验室、3家分成合作方、4个报表分类

### 4. 启动开发服务器

```bash
python manage.py runserver
```

访问: http://localhost:8000

## 模块结构

| 模块 | 路径 | 功能 |
|------|------|------|
| 仪表盘 | `/` | 首页统计与快捷入口 |
| 库存管理 | `/inventory/` | 保健品进销存、Excel导入导出 |
| 实验室账单 | `/lab-bills/` | 账单导入取数、手动打标签、多维筛选 |
| VIP管理 | `/vip/` | 会员档案、疗程、收款、费用分摊 |
| 分成管理 | `/revenue-share/` | 合作方配置、自动分成计算、对账 |
| 账单生成 | `/billing/` | ABC系统导入、按模板生成账单 |
| 每月报表 | `/reports/` | 动态报表项、在线编辑、按月筛选导出 |
| 前台收款 | `/frontdesk/` | 通联支付导入、收款标注、现金管理 |
| 后台管理 | `/admin/` | Django Admin（模型管理、自定义字段配置） |

## 角色权限

| 角色 | 可访问模块 |
|------|-----------|
| 管理员 | 所有模块 + 后台管理 |
| 前台 | 库存、实验室账单、VIP、前台收款、报表 |
| 库房 | 库存管理、实验室账单 |
| 合作方 | 分成管理、账单生成、报表 |

## 自定义字段系统

在 Admin 后台的「自定义字段定义」中添加字段，系统自动在对应实体的详情/编辑页显示。

支持类型: 文本、数字、日期、是/否、下拉选择

## 生产部署

```bash
# 设置环境变量
export DJANGO_DEBUG=False
export DJANGO_SECRET_KEY=your-secret-key
export DB_ENGINE=django.db.backends.postgresql
export DB_NAME=clinic_db
export DB_USER=clinic_user
export DB_PASSWORD=your-password
export DB_HOST=localhost
export DB_PORT=5432

# 收集静态文件
python manage.py collectstatic --noinput

# 使用 gunicorn
pip install gunicorn
gunicorn clinic_management.wsgi:application -w 4 -b 0.0.0.0:8000
```

## 数据库备份

```bash
# PostgreSQL 备份
pg_dump clinic_db > backup_$(date +%Y%m%d).sql

# SQLite 备份
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3
```
