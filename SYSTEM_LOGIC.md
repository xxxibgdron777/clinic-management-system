# 综合性诊所管理系统 — 完整配置逻辑与计算方式

> **技术栈**: Django 6.0 / Bootstrap 5.3 / pandas / openpyxl / SQLite  
> **GitHub**: https://github.com/xxxibgdron777/clinic-management-system

---

## 目录

1. [系统架构概览](#1-系统架构概览)
2. [权限角色体系](#2-权限角色体系)
3. [库存管理](#3-库存管理)
4. [实验室账单](#4-实验室账单)
5. [VIP会员管理](#5-vip会员管理)
6. [合作机构分成](#6-合作机构分成)
7. [账单生成](#7-账单生成)
8. [每月报表](#8-每月报表)
9. [前台收款](#9-前台收款)
10. [核心模块与系统配置](#10-核心模块与系统配置)

---

## 1. 系统架构概览

```
├── apps/core/          # 核心抽象基类 + 仪表盘 + 自定义字段系统
├── apps/accounts_app/  # 用户认证、角色权限
├── apps/inventory/     # M1: 保健品库存（进销存）
├── apps/lab_bills/     # M2: 实验室账单（5个合作实验室）
├── apps/vip/           # M3: VIP会员管理（疗程/收费/费用分摊）
├── apps/revenue_share/ # M4: 合作机构分成（3个合作方）
├── apps/billing/       # M5: 账单生成（ABC系统导入）
├── apps/reports/       # M6: 每月报表（动态项目）
├── apps/frontdesk/     # M7: 前台收款（通联支付）
```

---

## 2. 权限角色体系

### 2.1 角色定义

| 角色代码 | 中文名称 | 可访问模块 |
|----------|---------|-----------|
| `admin` | 管理员 | inventory, lab_bills, vip, revenue_share, billing, reports, frontdesk, accounts |
| `frontdesk` | 前台 | inventory, lab_bills, vip, frontdesk, reports |
| `warehouse` | 库房 | inventory, lab_bills |
| `partner` | 合作方 | revenue_share, billing, reports |

### 2.2 用户模型

```python
UserProfile:
  user        → OneToOneField(auth.User)
  role        → admin / frontdesk / warehouse / partner
  phone       → CharField
  department  → CharField

快捷属性: is_admin, is_frontdesk, is_warehouse, is_partner
```

### 2.3 访问控制

- 所有业务视图使用 `@login_required` 装饰器
- 登录页面: `/accounts/login/`
- 登录后跳转: `/`（仪表盘）
- 默认账户: `admin` / `admin123`

---

## 3. 库存管理

### 3.1 Product（商品）模型

| 字段 | 说明 |
|------|------|
| `name_cn` | 中文名称 |
| `name_en` | 英文名称 |
| `category` | 类别（默认"保健品"） |
| `unit` | 最小单位（瓶/盒/粒，默认"瓶"） |
| `cost_price` | 成本单价 |
| `selling_price` | 销售单价（默认=成本价） |
| `expiry_date` | 有效期 |
| `supplier` | 供应商/采购平台 |
| `current_stock` | 当前库存数量 |
| `min_stock_threshold` | 库存预警阈值（默认10） |
| `batch_number` | 批次号 |
| `barcode` | 条形码 |

#### 库存状态判断（stock_status）

| 条件 | 状态 |
|------|------|
| `current_stock ≤ 0` | **缺货** |
| `current_stock ≤ min_stock_threshold` | **低库存** |
| `current_stock > min_stock_threshold` | **正常** |

#### 显示名称（display_name）

```
display_name = "中文名 (英文名)"   # 有英文名时
display_name = "中文名"            # 无英文名时
```

---

### 3.2 StockIn（入库）计算

```
入库类型: purchase(采购入库) / return(退货入库) / adjust(盘点调整)

计算:
  total_amount = quantity × unit_price          # save() 时自动计算

副作用（新建 + 已确认时）:
  product.current_stock += quantity             # 自动增加库存
```

---

### 3.3 StockOut（出库）计算

```
出库类型: sale(销售出库) / scrap(报废出库)

计算:
  total_amount = quantity × unit_price          # save() 时自动计算

副作用（新建时）:
  product.current_stock -= quantity             # 自动减少库存
  if vip_member 存在 → customer_name 自动填充会员姓名
```

---

### 3.4 库存模块与外部的联动

- **VIP 费用项** (`VIPCostItem.stock_out_records`)：关联出库记录，建立"保健品费用→实际出库"的对账链接
- **仪表盘**：展示活跃商品数量和最新10条出库记录

---

## 4. 实验室账单

### 4.1 LabPartner（合作实验室）

5 个合作方（系统数据初始化时创建）：

| 简称 | 全称 |
|------|------|
| 华测 | 华测检测 |
| 迪恩 | 迪安诊断 |
| 华莱士 | 华莱士医学检验 |
| 鼎坤 | 鼎坤医学检验 |
| 博厚 | 博厚医学检验 |

---

### 4.2 LabBillRecord（账单记录）标签体系

#### 付款人（PAYER_CHOICES）

| 代码 | 中文标签 |
|------|---------|
| `personal` | 个人 |
| `taikang` | 泰康 |
| `msh` | MSH |
| `pingan` | 平安 |
| `hongkong` | 香港 |
| `union` | 平台工会 |

#### 科室（DEPARTMENT_CHOICES）

| 代码 | 中文标签 |
|------|---------|
| `health_mgmt` | 健康管理 |
| `daily_med` | 日常医疗 |

#### 项目（PROJECT_CHOICES）

| 代码 | 中文标签 |
|------|---------|
| `anti_aging` | 抗衰老 |
| `anti_aging_first` | 抗衰老首次血检 |
| `lifestyle` | 生活方式门诊 |
| `lifestyle_first` | 生活方式门诊首次血检 |
| `hormone` | 荷尔蒙 |
| `hormone_first` | 荷尔蒙首次血检 |
| `gut_flora` | 肠道菌群 |
| `alzheimers` | 阿尔兹海默症 |
| `glucose` | 血糖代谢检测 |
| `routine` | 其他常规门诊 |

---

### 4.3 筛选汇总计算（get_filter_summary）

对当前筛选后的查询集进行计算：

```
total_count    = queryset.count()                          # 记录条数
total_quantity = SUM(test_quantity)                        # 合计数量
total_amount   = SUM(settlement_price)                     # 合计金额（折后）
```

---

### 4.4 Excel 导入智能列映射（_detect_columns）

系统自动识别 Excel 列名（中英文均可）：

| 识别关键词 | 映射字段 |
|-----------|---------|
| 客户/姓名/customer/name/客户姓名 | `customer` |
| 检测日期/日期/date/test date | `test_date` |
| 套餐/检测项目/package/test/项目名称 | `test_package` |
| 编码/code/套餐编码 | `package_code` |
| 数量/quantity/qty | `quantity` |
| 标准单价/标准价格/standard/单价 | `standard_price` |
| 折扣/discount | `discount` |
| 结算/折后/settlement/实际 | `settlement_price` |
| 付款人/付款/payer | `payer` |
| 科室/部门/department/dept | `department` |
| 项目/project/归类 | `project` |

---

### 4.5 标签导入映射（中文→代码）

导入时 Excel 中的中文标签自动映射为模型代码：

| Excel 值 | 映射结果 |
|----------|---------|
| 个人 | `personal` |
| 泰康 | `taikang` |
| MSH / msh | `msh` |
| 平安 | `pingan` |
| 香港 | `hongkong` |
| 平台工会 / 工会 | `union` |
| 健康管理 | `health_mgmt` |
| 日常医疗 | `daily_med` |
| 抗衰老 | `anti_aging` |
| 抗衰老首次血检 | `anti_aging_first` |
| 生活方式门诊 | `lifestyle` |
| 生活方式门诊首次血检 | `lifestyle_first` |
| 荷尔蒙 | `hormone` |
| 荷尔蒙首次血检 | `hormone_first` |
| 肠道菌群 | `gut_flora` |
| 阿尔兹海默症 | `alzheimers` |
| 血糖代谢检测 | `glucose` |
| 其他常规门诊 | `routine` |

**标签优先级**：Excel 列值 > 表单默认值 > 留空

---

### 4.6 重复判断逻辑

```
同一合作方 + 同一客户姓名 + 同一检测日期 + 同一检测套餐 → 视为重复
勾选"跳过重复"后自动跳过
```

---

### 4.7 批量删除

```
POST /lab-bills/records/batch-delete/
参数: record_ids = [pk1, pk2, ...]
前端: 复选框选择 → form.onsubmit 校验（至少选1条）→ confirm 确认
```

---

## 5. VIP会员管理

### 5.1 VIPMember（会员档案）

| 关键字段 | 说明 |
|---------|------|
| `name` | 姓名（索引） |
| `gender` | M(男) / F(女) |
| `phone` | 电话 |
| `birth_date` | 出生日期 |
| `id_number` | 证件号 |
| `address` | 地址 |
| `is_active` | 活跃状态 |

---

### 5.2 VIPCourse（疗程）

| 字段 | 说明 |
|------|------|
| `member` | FK→VIPMember |
| `duration_months` | 疗程时长：3个月 / 6个月 / 12个月 |
| `total_price` | 疗程总价（范围：3万-25万） |
| `start_date` | 开始日期 |
| `end_date` | 结束日期（**自动计算**） |
| `attending_doctor` | 合作医生 |
| `status` | active(进行中) / completed(已完成) / paused(已暂停) |

#### ① 自动计算结束日期（save 方法）

```python
end_date = start_date + relativedelta(months=duration_months) - 1 day

# 例: 2024-01-15 开始，6个月疗程
# end_date = 2024-07-14
```

#### ② 月度收入确认金额（monthly_revenue）

```python
monthly_revenue = total_price / duration_months

# 例: 6万/6个月=1万/月（线性摊销）
```

---

### 5.3 VIPPayment（收款记录）

| 字段 | 说明 |
|------|------|
| `member` | FK→VIPMember |
| `course` | FK→VIPCourse（可选） |
| `amount` | 收款金额 |
| `payment_date` | 收款日期 |
| `project_type` | 项目类型（首次门诊、疗程费用、药费等） |

---

### 5.4 VIPCostItem（疗程费用项）

#### 费用类型（COST_TYPES）

| 代码 | 中文 | 说明 |
|------|------|------|
| `first_visit` | 首次门诊+血检 | 首诊费用 |
| `injection` | 点滴注射 | 可从Excel导入 |
| `supplements` | 餐包及营养补给 | 保健品费用 |
| `blood_test` | 血检 | 血液检测 |
| `imaging` | 影像 | 影像检查 |
| `nurse_labor` | 护士人工 | 护理人力成本 |
| `reception` | 客户接待 | 接待服务成本 |
| `fixed_cost` | 固定费用 | 可配置"按疗程均摊" |
| `other` | 其他自定义 | 可用custom_name自定义 |

#### 费用项金额字段

| 字段 | 说明 |
|------|------|
| `standard_amount` | 标准/参考金额 |
| `cost_amount` | 实际成本金额 |
| `total_amount` | 此项费用总金额 |

#### ③ 按疗程均摊计算（allocated_amount）

```python
if is_per_course = True:
    # 统计同一 cost_type + custom_name 下的不同疗程数
    course_count = 去重疗程数（至少为1）
    allocated_amount = total_amount / course_count
else:
    allocated_amount = total_amount
```

#### 外部关联

| 关联字段 | 说明 |
|---------|------|
| `lab_bill_records` | M2M→LabBillRecord（关联血检/影像账单） |
| `stock_out_records` | M2M→StockOut（关联保健品出库） |

---

### 5.5 VIPRevenueRecognition（收入确认）

```
每条记录 = 会员 + 疗程 + 年份 + 月份 + 确认金额
唯一约束: (course, year, month)

确认金额 = course.monthly_revenue（即 total_price / duration_months）
```

---

### 5.6 点滴及针剂费用 Excel 导入

```
POST /vip/injection/import/
表单: member(必选) + course(可选) + excel_file + skip_duplicates

智能列识别:
  日期 / 项目名称 / 数量 / 单价 / 金额

重复规则: 同一会员 + 日期 + 项目名称 → 跳过
导入结果: 写入 VIPCostItem（cost_type='injection'）
```

---

## 6. 合作机构分成

### 6.1 RevenuePartner（合作方）

3 个合作方：

| 合作方 | 关联项目 |
|--------|---------|
| 香港机构 | anti_aging（抗衰老） |
| 叶医生 | lifestyle（生活方式门诊） |
| 杨医生 | hormone（荷尔蒙） |

---

### 6.2 RevenueShareConfig（分成配置）

每个合作方一对一配置，7 项可扣除费用均可独立开关：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|-------|------|
| `deduction_rate` | Decimal(5,4) | 0.10 (10%) | 护士/接待费扣除比例 |
| `partner_share_ratio` | Decimal(5,4) | 0.50 (50%) | 合作方分成比例 |
| `deduct_lab_bills` | Boolean | True | 扣除实验室费用 |
| `deduct_supplements` | Boolean | True | 扣除保健品费用 |
| `deduct_imaging` | Boolean | True | 扣除影像费用 |
| `deduct_nurse` | Boolean | True | 扣除护士人工 |
| `deduct_reception` | Boolean | True | 扣除客户接待 |
| `deduct_travel` | Boolean | True | 扣除差旅费 |
| `deduct_fixed` | Boolean | True | 扣除固定费用 |

---

### 6.3 分成计算公式（calculation_run）

```
步骤:
┌─────────────────────────────────────────────────────┐
│ 1. 取当月全部 VIPCostItem                            │
│    total_revenue = SUM(total_amount)                 │
│                                                      │
│ 2. 按开关汇总可扣项（deduct_* = True 时累加）:          │
│    deduct_lab_bills   → SUM(cost_type='blood_test')   │
│    deduct_imaging     → SUM(cost_type='imaging')       │
│    deduct_nurse       → SUM(cost_type='nurse_labor')   │
│    deduct_reception   → SUM(cost_type='reception')     │
│    deduct_supplements → SUM(cost_type='supplements')   │
│    deduct_travel      → (预留, 当前无直接对应)           │
│    deduct_fixed       → (预留, 当前无直接对应)           │
│                                                      │
│ 3. nurse_reception_deduction = total_revenue × deduction_rate │
│                                                      │
│ 4. total_deductions = 可扣项合计 + nurse_reception_deduction  │
│                                                      │
│ 5. net_revenue = total_revenue - total_deductions     │
│                                                      │
│ 6. partner_share = net_revenue × partner_share_ratio  │
└─────────────────────────────────────────────────────┘
```

**举例**（香港机构，deduction_rate=10%, share_ratio=50%，全开）：

```
总收入:           100,000
可扣项合计:         27,500 (血检15k+影像5k+护士3k+接待2k+保健品2.5k)
护士/接待费扣除:    10,000 (=100k × 10%)
总扣除:            37,500
净收入:            62,500
应付分成:          31,250 (=62,500 × 50%)
```

---

### 6.4 状态流转

```
RvenueShareCalculation:
  draft → confirmed → settled

ReconciliationStatement:
  draft → sent → confirmed
```

---

## 7. 账单生成

### 7.1 BillImport（ABC系统导入）

| 字段 | 说明 |
|------|------|
| `customer_name` | 客户姓名 |
| `bill_date` | 日期 |
| `item_name` | 项目名称 |
| `unit_price` | 单价 |
| `quantity` | 数量 |
| `amount` | 金额（人民币） |
| `hkd_amount` | 港币金额 |
| `source_file` | 来源文件名 |

---

### 7.2 BillTemplate（账单模板）

```python
name          # 模板名称
description   # 说明
partner_type  # 适用合作方
fields_config # JSON: 字段定义列表
is_active     # 是否启用
```

---

### 7.3 GeneratedBill（已生成账单）

| 字段 | 说明 |
|------|------|
| `template` | 关联模板 |
| `partner_name` | 合作方 |
| `year` / `month` | 年月 |
| `bill_data` | JSON 账单明细数据 |
| `total_amount` | 人民币总金额 |
| `hkd_total` | 港币总金额 |
| `status` | draft → generated → sent |

---

## 8. 每月报表

### 8.1 ReportCategory（报表分类）

4 个分类（初始化时创建）：

| 分类 | 可在线编辑 | 说明 |
|------|----------|------|
| 业务对象 | 否 | 主要业务指标 |
| 功能医学 | 否 | 功能医学项目 |
| 运动康复 | **是** | 支持在线编辑行数据 |
| 神经康复 | **是** | 支持在线编辑行数据 |

---

### 8.2 ReportItem（报表项目）

```python
category     # FK→ReportCategory
name         # 项目名称
description  # 说明
unit_price   # 单价
order        # 排序
is_active    # 是否启用
```

---

### 8.3 MonthlyReportEntry（月度数据录入）

```python
report_item  # FK→ReportItem
year / month # 年月（唯一约束一条目一个月一条）
quantity     # 数量
amount       # 金额
notes        # 备注
```

```
唯一约束: (report_item, year, month)
```

---

## 9. 前台收款

### 9.1 PaymentRecord（收款记录）

#### 收费类型（PAYMENT_TYPES）

| 代码 | 中文 |
|------|------|
| `outpatient` | 门诊 |
| `lab` | 检测 |
| `medication` | 药费 |
| `injection` | 打针/输液 |
| `supplements` | 保健品 |
| `other` | 其他 |

#### 付款方类型（PAYER_TYPES）

| 代码 | 中文 |
|------|------|
| `self` | 自费 |
| `pingan` | 平安保险 |
| `msh` | MSH保险 |
| `taikang` | 泰康保险 |
| `corporate` | 企业合作 |

#### 附加追踪字段

| 字段 | 说明 |
|------|------|
| `transaction_ref` | 通联支付交易流水号 |
| `insurance_claimed` | 是否已申请理赔 |
| `insurance_claim_date` / `insurance_status` | 理赔进度 |
| `invoiced` / `invoice_number` | 发票管理 |

---

### 9.2 CashRecord（现金管理）

| 类型 | 代码 |
|------|------|
| 收款 | `income` |
| 支出 | `expense` |
| 报销 | `reimburse` |

每条记录包含：日期、类型、金额、说明、收付款人、费用类别。

---

## 10. 核心模块与系统配置

### 10.1 自定义字段系统

支持为**任意模型**动态添加自定义字段：

```
CustomFieldDefinition:
  entity_type  → ContentType（如 'lab_bill', 'customer'）
  field_name   → 字段名称
  field_type   → text / number / date / boolean / select
  options      → select类型时的下拉选项（按行分隔）
  is_required  → 是否必填
  order        → 排序

CustomFieldValue:
  definition   → FK→CustomFieldDefinition
  content_type + object_id → GenericFK（关联具体实例）
  value_text   → 文本值
  value_number → 数值
  value_date   → 日期值
  value_boolean→ 布尔值

唯一约束: (definition, content_type, object_id)
```

---

### 10.2 SystemConfig（系统级配置）

```python
# 获取配置值（自动类型转换）
value = SystemConfig.get('config_key', default_value)

# 支持类型:
config_type = text / number / json / boolean
```

---

### 10.3 Django 配置项速查

| 配置项 | 值 | 说明 |
|--------|---|------|
| `LANGUAGE_CODE` | `zh-hans` | 简体中文 |
| `TIME_ZONE` | `Asia/Shanghai` | 上海时区 |
| `LOGIN_URL` | `/accounts/login/` | 登录页面 |
| `DATA_UPLOAD_MAX_NUMBER_FIELDS` | 10000 | 表单字段数上限 |
| `FILE_UPLOAD_MAX_MEMORY_SIZE` | 10MB | 文件上传限制 |
| `DEBUG` | True | 开发模式 |

---

## 附录：模块间数据流关系

```
                    ┌─────────────────────┐
                    │   LabBillRecord      │
                    │  (实验室账单记录)      │
                    └─────────┬───────────┘
                              │ M2M
                    ┌─────────▼───────────┐
                    │    VIPCostItem       │◄── Excel导入(点滴/针剂)
                    │   (VIP疗程费用项)     │
                    └─────────┬───────────┘
                              │ M2M         │ 累加汇总
                    ┌─────────▼───┐  ┌─────▼───────────┐
                    │  StockOut    │  │RevenueShareCalc  │
                    │ (保健品出库)  │  │  (合作分成计算)    │
                    └─────────────┘  └─────┬───────────┘
                                           │
                              ┌────────────▼───────────┐
                              │  ReconciliationStatement│
                              │      (对账单)            │
                              └────────────────────────┘

  VIPCourse ──→ VIPRevenueRecognition（按月摊销收入）
  BillImport ──→ GeneratedBill（ABC系统→账单生成）
  PaymentRecord ──→ 通联支付导入 + 保险理赔
```
