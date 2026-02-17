# 代码去重 B组 报告

## 概述

本报告记录了 B 组（audits, bom, bonus, budget, business_support, ecn 等）的代码去重重构工作。

**重构方式**：使用 `app.utils.db_helpers` 工具函数替换重复的数据库操作模式。  
**已包含于提交**：`662b0422 refactor(D-group): 使用 db_helpers 消除 projects/purchase/sales 重复代码`

---

## 统计汇总

| 指标 | 数量 |
|------|------|
| 处理文件总数 | 45 |
| 实际修改文件数 | 34 |
| 未变更文件数 | 11 |
| `get_or_404` 替换总数 | 81 |
| `save_obj` 替换总数 | 1 |
| 新增 import 次数 | 34 |
| **消除重复代码行数** | **~244 行** |

---

## 修改详情

| 文件 | get_or_404 | save_obj | +import |
|------|------------|----------|---------|
| `audits.py` | 1 | - | ✓ |
| `bom/bom_detail.py` | - | - | ✓ |
| `bom/bom_items.py` | - | - | ✓ |
| `bom/bom_versions.py` | - | - | ✓ |
| `bonus/allocation_sheets/crud.py` | 1 | - | ✓ |
| `bonus/allocation_sheets/download.py` | 1 | - | ✓ |
| `bonus/allocation_sheets/operations.py` | 2 | - | ✓ |
| `bonus/allocation_sheets/rows.py` | 1 | - | ✓ |
| `bonus/payment.py` | 2 | - | ✓ |
| `bonus/rules.py` | 5 | - | ✓ |
| `bonus/sales_calc.py` | 2 | - | ✓ |
| `bonus/team.py` | 2 | - | ✓ |
| `budget/allocation_rules.py` | 3 | - | ✓ |
| `budget/budgets.py` | 6 | - | ✓ |
| `budget/items.py` | 4 | - | ✓ |
| `business_support/bidding.py` | 2 | - | ✓ |
| `business_support/contract_review.py` | 1 | - | ✓ |
| `business_support/contract_seal.py` | 1 | - | ✓ |
| `business_support_orders/delivery_orders/crud.py` | 2 | - | ✓ |
| `business_support_orders/invoice_requests.py` | 5 | - | ✓ |
| `business_support_orders/reconciliations.py` | 3 | - | ✓ |
| `business_support_orders/sales_orders/crud.py` | 2 | - | ✓ |
| `business_support_orders/sales_orders/operations.py` | 2 | - | ✓ |
| `business_support_orders/tracking_crud.py` | 2 | - | ✓ |
| `business_support_orders/tracking_operations.py` | 2 | - | ✓ |
| `culture_wall/contents.py` | 1 | - | ✓ |
| `documents/crud_refactored.py` | 3 | - | ✓ |
| `documents/operations.py` | 4 | 1 | ✓ |
| `ecn/approval.py` | 1 | - | ✓ |
| `ecn/core.py` | 4 | - | ✓ |
| `ecn/evaluations.py` | 5 | - | ✓ |
| `ecn/execution.py` | 3 | - | ✓ |
| `ecn/impacts.py` | 4 | - | ✓ |
| `ecn/integration.py` | 4 | - | ✓ |

---

## 未变更文件（11个）

以下文件无可安全替换的明确模式：

| 文件 | 原因 |
|------|------|
| `backup.py` | 使用 Service 层，无直接 DB 操作 |
| `bonus/calculation.py` | 批量操作模式，不适合单条替换 |
| `business_support/payment_reminders.py` | 无匹配的 `Model.id == id` 过滤模式 |
| `business_support_orders/customer_registrations.py` | 多条件过滤（含业务逻辑），不适合简单替换 |
| `business_support_orders/sales_reports.py` | 只读报表，无 CRUD 操作 |
| `change_impact.py` | 使用服务层和复杂过滤条件 |
| `culture_wall/goals.py` | 使用 `and_()` 多条件过滤，不匹配简单模式 |
| `customers/view360.py` | 使用 Service 层，无直接 DB 操作 |
| `dashboard/cost_dashboard.py` | 报表聚合查询，无简单 CRUD |
| `dashboard_unified.py` | 模块路由，无 DB 操作 |
| `departments/__init__.py` | 已使用自定义服务方法 |

---

## 替换模式示例

### 规则1：查询 + 404 模式

**替换前：**
```python
rule = db.query(BonusRule).filter(BonusRule.id == rule_id).first()
if not rule:
    raise HTTPException(status_code=404, detail="规则不存在")
```

**替换后：**
```python
rule = get_or_404(db, BonusRule, rule_id, "规则不存在")
```

### 规则2：add + commit + refresh + return 模式

**替换前：**
```python
db.add(document)
db.commit()
db.refresh(document)
return document
```

**替换后：**
```python
return save_obj(db, document)
```

---

## 语法验证

所有 34 个修改文件均通过 Python AST 语法验证（`python3 -c "import ast; ast.parse(...)"`）。

---

## 工具脚本

重构使用的自动化脚本：`refactor_b_group.py`

该脚本使用正则表达式精确匹配以下模式：
1. `db.query(Model).filter(Model.id == id_var).first()` + `if not obj: raise HTTPException(status_code=404, ...)`
2. `db.add(obj)` + `db.commit()` + `db.refresh(obj)` + `return obj`

并使用 AST 分析定位顶层 import 末尾位置，安全插入 `from app.utils.db_helpers import get_or_404, save_obj, delete_obj`。
