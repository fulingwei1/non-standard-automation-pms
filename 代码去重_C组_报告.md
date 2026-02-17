# 代码去重 C 组报告

**日期**: 2026-02-17  
**Git Commit**: `0fbae9b2` (refactor(C-group): 使用 db_helpers 消除 engineers/presale/production 重复代码)  
**处理范围**: engineer*, material*, notification, presale*, production* 相关端点

---

## 执行摘要

- **处理文件总数**: 25 个文件（10 个由 E-group 子 Agent 顺带处理，15 个由本次 C-group 脚本处理）
- **总 `get_or_404` 替换**: 61 处 `raise HTTPException(404)` 模式
- **总 `save_obj` 替换**: 12 处 `db.add/commit/refresh/return` 模式
- **跳过模式**: 28 处（复杂 filter、service 调用、f-string 详情等）
- **语法错误**: 0（所有修改文件通过 `ast.parse` 检查）

---

## 已处理文件

### C-group 专属提交（commit `0fbae9b2`）—— 5 个文件

| 文件 | get_or_404 | save_obj | 说明 |
|------|:---:|:---:|------|
| `app/api/v1/endpoints/bonus/payment.py` | 3 | 0 | 多行 filter 含点号属性 |
| `app/api/v1/endpoints/engineers/tasks.py` | 2 | 0 | 单行 + 点号属性 ID |
| `app/api/v1/endpoints/production/exception_enhancement.py` | 3 | 2 | 多行 filter + 空行分隔 |
| `app/api/v1/endpoints/production/quality.py` | 2 | 1 | 多行 filter + 空行 |
| `app/api/v1/endpoints/production/schedule.py` | 1 | 0 | 多行 filter + 空行 |

### E-group 子 Agent 顺带处理（commit `baf4d3bf`）—— 10 个 C-group 相关文件

| 文件 | get_or_404 | save_obj |
|------|:---:|:---:|
| `app/api/v1/endpoints/business_support/payment_reminders.py` | 1 | 0 |
| `app/api/v1/endpoints/engineer_performance/data_collection.py` | 4 | 0 |
| `app/api/v1/endpoints/engineer_performance/summary.py` | 1 | 0 |
| `app/api/v1/endpoints/engineers/progress.py` | 1 | 0 |
| `app/api/v1/endpoints/outsourcing/payments/crud.py` | 1 | 0 |
| `app/api/v1/endpoints/presale/tickets/crud.py` | 2 | 1 |
| `app/api/v1/endpoints/production/capacity/calculation.py` | 2 | 2 |
| `app/api/v1/endpoints/production/plans.py` | 7 | 2 |
| `app/api/v1/endpoints/production/work_orders/assignment.py` | 3 | 1 |
| `app/api/v1/endpoints/production/work_orders/crud.py` | 6 | 1 |
| `app/api/v1/endpoints/production/work_reports.py` | 5 | 0 |
| `app/api/v1/endpoints/production/workshops.py` | 5 | 2 |

### C-group 脚本处理的其他文件（在 E-group commit 之前由 v1-v4 脚本写入）

| 文件 | get_or_404 | save_obj |
|------|:---:|:---:|
| `app/api/v1/endpoints/assembly_kit/material_mapping.py` | 2 | 0 |
| `app/api/v1/endpoints/engineers/delays.py` | 1 | 0 |
| `app/api/v1/endpoints/engineers/proofs.py` | 3 | 0 |
| `app/api/v1/endpoints/engineers/visibility.py` | 1 | 0 |
| `app/api/v1/endpoints/material_demands/forecast.py` | 1 | 0 |
| `app/api/v1/endpoints/outsourcing/payments/print.py` | 1 | 0 |
| `app/api/v1/endpoints/presale_analytics/salesperson.py` | 1 | 0 |
| `app/api/v1/endpoints/technical_review/materials.py` | 2 | 0 |

---

## 跳过的模式（不安全或无法自动替换）

以下 28 处保持原样，原因如下：

### 1. Service 层调用（非 db.query）
| 文件 | 说明 |
|------|------|
| `presale_ai_emotion.py` (3处) | `service.get_emotion_trend()` 等 service 方法调用 |
| `engineer_performance/config.py` (1处) | `service.get_dimension_config()` |
| `engineer_performance/engineer.py` (4处) | `service.get_engineer_profile()` / `update_engineer_profile()` |
| `engineer_performance/knowledge.py` (3处) | `service.get_contribution()` / `update_contribution()` |
| `alerts/notifications.py` (1处) | `service.mark_notification_read()` 返回布尔值 |
| `presale_ai_integration.py` (1处) | `service.get_workflow_status()` + f-string 详情 |

### 2. 非 id 字段过滤（is_active、schedule_plan_id 等）
| 文件 | 说明 |
|------|------|
| `engineer_performance/ranking.py` (1处) | `PerformancePeriod.is_active` 过滤，非 id |
| `engineer_performance/summary.py` (2处) | `PerformancePeriod.is_active` 过滤 |
| `engineer_performance/data_collection.py` (3处) | `PerformancePeriod.is_active` 过滤 |
| `engineer_performance/collaboration.py` (3处) | `if not period_id:` 检查 ID 值非查询结果 |

### 3. 多条件 filter（含业务约束）
| 文件 | 说明 |
|------|------|
| `outsourcing/payments/crud.py` (1处) | `Vendor.id == x AND vendor_type == 'OUTSOURCING'` |
| `outsourcing/payments/statement.py` (1处) | 同上 |

### 4. f-string 或动态 detail
| 文件 | 说明 |
|------|------|
| `presale_analytics/resource_analysis.py` (1处) | `detail=f"未找到线索/项目: {lead_id}"` |
| `production/quality.py` (2处) | `detail=str(e)` 来自 ValueError |

### 5. 复杂查询链（joinedload / .all() / chaining）
| 文件 | 说明 |
|------|------|
| `sales/payments/payment_records.py` (1处) | `.options(joinedload(...)).filter(...)` 链式查询 |
| `notifications/crud_refactored.py` (2处) | 复杂多行链式查询 |
| `production/schedule.py` (3处) | `.all()` 查询（非 .first()）/ 复杂多条件 |
| `engineers/proofs.py` (1处) | 多条件复杂 filter |
| `exception_enhancement.py` (1处) | `exception_id` 字段（非 id）过滤 |

---

## 替换模式示例

### 规则1：查询+404 单行版
```python
# Before
project = db.query(Project).filter(Project.id == project_id).first()
if not project:
    raise HTTPException(status_code=404, detail="项目不存在")

# After
project = get_or_404(db, Project, project_id, "项目不存在")
```

### 规则1-B：查询+404 多行 filter 版（点号属性 ID）
```python
# Before
equipment = db.query(Equipment).filter(
    Equipment.id == request.equipment_id
).first()
if not equipment:
    raise HTTPException(status_code=404, detail="设备不存在")

# After
equipment = get_or_404(db, Equipment, request.equipment_id, "设备不存在")
```

### 规则2：db.add/commit/refresh/return
```python
# Before
db.add(obj)
db.commit()
db.refresh(obj)
return obj

# After
return save_obj(db, obj)
```

---

## 脚本迭代记录

| 版本 | 改进点 | 结果 |
|------|--------|------|
| v1 | 基础单行替换 | 9 文件，2 语法错误（多行 import 插入位置错误） |
| v2 | 修复 import 插入：仅跟踪顶层 import | 2 文件，1 语法错误（函数内 import） |
| v3 | 仅匹配无缩进的顶层 import 行 | 1 文件，0 错误 |
| v4 | 新增多行 filter 模式（单 id 条件）+ 点号属性 | 11 文件，0 错误 |
| v5 | 新增可选空行 + 点号属性扩展 | 5 文件，0 错误 |

---

## 验证

所有修改文件通过语法检查：
```bash
python3 -c "import ast; ast.parse(open('文件路径').read()); print('OK')"
```

Git commit: `0fbae9b2`  
修改行数: -32 行（净减少）
