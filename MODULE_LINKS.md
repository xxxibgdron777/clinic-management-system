# 诊所管理系统 — 模块关联逻辑

## 核心实体链

```
Partner(合作商) → Project(项目) → 一切数据源
                     ↓
              RevenueShareConfig(分成配置)
```

---

## 一、合作商与项目

```
Partner (香港巴黎/叶医生/杨医生/老干局/平台工会/其他)
  │
  └── Project (15个)  ─────────── RevenueShareConfig (1:1，每项目独立分成)
       ├── name         项目全称  "香港巴黎 首次血检"
       ├── short_name   项目简称  "抗衰老首次血检"
       ├── project_type 类型      first_test / course_mgmt
       └── duration_months 疗程月数
```

---

## 二、四大数据源 → 月度报表

```
┌──────────────────────────────────────────────────────────┐
│                   MonthlyReport (月度报表)                │
│  project(→Project) + year + month                        │
│  ├── payment_income    ← 前台收款 SUM                     │
│  ├── cost_details      ← 费用科目明细(JSON)                │
│  ├── service_fee       ← 护士服务费                       │
│  ├── deductible_cost   ← 可扣除费用                       │
│  ├── share_base        ← 分成基数                         │
│  └── share_amount      ← 应付分成                         │
└──────────────────────────────────────────────────────────┘
         ↑                ↑              ↑              ↑
    前台收款          实验室账单       库存出库        手工费用
  PaymentRecord    LabBillRecord    StockOut      ManualCostEntry
```

### 各数据源字段

| 数据源 | 关联 Project | 关联 VIPMember | 关联其他 |
|--------|:-----------:|:-------------:|---------|
| **PaymentRecord** 前台收款 | `project` FK | `vip_member` FK | payer_type, payment_type |
| **LabBillRecord** 实验室账单 | `project` FK | `vip_member` FK | `lab_partner` FK |
| **StockOut** 库存出库 | `project` FK | `vip_member` FK | `product` FK, `cost_category` FK |
| **ManualCostEntry** 手工费用 | `project` FK | — | `category` FK(CostCategory) |

---

## 三、VIP会员联动

```
VIPMember (会员档案)
  member_number = "000001" (6位自动编号)
  name, phone, gender, birth_date

  关联数据:
  ├── frontdesk_payments   ← PaymentRecord (related_name)
  ├── lab_bill_records     ← LabBillRecord (related_name)
  ├── stock_outs           ← StockOut (related_name)
  ├── courses              ← VIPCourse
  ├── payments             ← VIPPayment (VIP模块内部收款)
  └── cost_items           ← VIPCostItem
```

---

## 四、库存出库 → 费用科目自动映射

```
Product.category → CostCategory
  ├── injection(打针类) → "打针"
  └── supplement(补剂类) → "补剂"

StockOut.save() 时自动匹配:
  1. 根据 product.category 查找对应 CostCategory
  2. 设置 stockout.cost_category
```

---

## 五、月度报表计算逻辑

```
calculate_monthly_report(project, year, month)

1. 前台收款收入 = SUM(PaymentRecord.amount)
     WHERE project=project AND date within year-month

2. 费用明细 (cost_details JSON):
   a) 实验室血检    = SUM(LabBillRecord.settlement_price)
   b) 库存出库      = SUM(StockOut.total_amount) GROUP BY cost_category
   c) 手工费用      = SUM(ManualCostEntry.amount) GROUP BY category

3. 费用合计 = SUM(所有费用)

4. 护士服务费 = 收款收入 × nurse_fee_rate  [仅当勾选"护士服务费"科目]
5. 可扣除费用 = Σ(勾选科目的费用)         [排除护士服务费]
6. 分成基数   = 收款收入 - 护士服务费 - 可扣除费用
7. 应付分成   = 分成基数 × share_ratio
```

---

## 六、分成配置 (RevenueShareConfig)

```
每项目 1:1 独立配置:
  ├── share_ratio        分成比例 (如 50%)
  ├── nurse_fee_rate     护士服务费比例 (如 10%)
  ├── deductible_categories  M2M → CostCategory (勾选可扣除科目)
  └── save_history()     每次修改自动存档

RevenueShareConfigHistory:
  记录每次修改的 分成比例、护士服务费比例、勾选科目列表
```

---

## 七、统一费用科目库 (CostCategory)

```
8个科目:
  1. 打针        (order=1)
  2. 补剂        (order=2)
  3. 护士服务费  (order=3) ← 特殊: 收入×比例 而非实际成本
  4. 影像检查    (order=4)
  5. 中期血检    (order=5)
  6. 客户接待费  (order=6)
  7. 差旅费      (order=7)
  8. 其他        (order=99)

关联:
  ├── RevenueShareConfig.deductible_categories (M2M)
  ├── StockOut.cost_category (FK)
  ├── ManualCostEntry.category (FK)
  └── ProjectCategoryConfig (每项目可启用/禁用)
```

---

## 八、导入时的自动联动

| 导入模块 | VIP会员 | 项目Project | 其他 |
|---------|:------:|:---------:|------|
| 实验室账单 | 按客户姓名精确匹配 | 5层匹配: 精确→简名→去前缀→模糊→类型名 | 付款人/科室映射 |
| 前台收款 | 按客户姓名精确匹配 | 简名→全名→模糊 | 流水号记录 |
| 库存入库 | — | — | 商品名模糊匹配 |
| VIP会员批量 | — | — | 档案号自动6位格式化 |

---

## 九、数据库外键关系总表

| 源表 | 字段 | 目标表 | 类型 |
|------|------|--------|------|
| Project | partner | Partner | FK |
| RevenueShareConfig | project | Project | OneToOne |
| RevenueShareConfig | deductible_categories | CostCategory | M2M |
| PaymentRecord | project | Project | FK(nullable) |
| PaymentRecord | vip_member | VIPMember | FK(nullable) |
| LabBillRecord | project | Project | FK(nullable) |
| LabBillRecord | vip_member | VIPMember | FK(nullable) |
| LabBillRecord | lab_partner | LabPartner | FK |
| StockOut | project | Project | FK(nullable) |
| StockOut | vip_member | VIPMember | FK(nullable) |
| StockOut | product | Product | FK |
| StockOut | cost_category | CostCategory | FK(nullable) |
| ManualCostEntry | project | Project | FK |
| ManualCostEntry | category | CostCategory | FK |
| MonthlyReport | project | Project | FK |
| VIPCourse | member | VIPMember | FK |
| RevenueShareConfigHistory | project | Project | FK |
| ProjectCategoryConfig | project | Project | FK |
| ProjectCategoryConfig | category | CostCategory | FK |
