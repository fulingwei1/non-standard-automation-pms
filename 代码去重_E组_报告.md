# 代码去重报告 - E组

**执行时间**: 2026-02-17  
**执行范围**: sales / service / staff_matching / standard_costs / task_center / technical_review / users 等模块  
**Git Commit**: `baf4d3bf` - refactor(E-group): 使用 db_helpers 消除 sales/service/staff/task/timesheet/users 重复代码

---

## 执行摘要

| 指标 | 数值 |
|------|------|
| 处理文件总数 | 71 |
| 成功修改文件 | 33 |
| 无变更文件 | 38 |
| 错误文件 | 0 |
| 规则1替换(get_or_404) | 67 处 |
| 规则2替换(save_obj) | 12 处 |
| Git 变更 | 46 files, +206/-380 行（净减 174 行） |

---

## 替换规则说明

### 规则1: query + 404 → get_or_404()

```python
# Before (3行)
obj = db.query(SomeModel).filter(SomeModel.id == some_id).first()
if not obj:
    raise HTTPException(status_code=404, detail="xxx")

# After (1行)
obj = get_or_404(db, SomeModel, some_id, "xxx")
```

**安全限制**: 只替换 `detail` 为简单字符串字面量（不含 f-string 或变量），避免破坏动态错误信息。

### 规则2: db.add + commit + refresh + return → save_obj()

```python
# Before (4行)
db.add(obj)
db.commit()
db.refresh(obj)
return obj

# After (1行)
return save_obj(db, obj)
```

**安全限制**: 只替换四行连续出现的模式，非连续的（中间有其他逻辑）不替换。

---

## 修改文件详情

### sales 模块

| 文件 | 规则1 | 规则2 | import |
|------|-------|-------|--------|
| sales/contacts.py | 3 处 | - | 已添加 |
| sales/customers.py | 2 处 | - | 已扩展 |

### service 模块

| 文件 | 规则1 | 规则2 | import |
|------|-------|-------|--------|
| service/communications.py | 2 处 | 2 处 | 已添加 |
| service/knowledge/crud.py | 3 处 | 3 处 | 已添加 |
| service/knowledge/download.py | 1 处 | - | 已添加 |
| service/knowledge/interactions.py | 3 处 | 3 处 | 已添加 |
| service/records.py | 2 处 | - | 已添加 |
| service/survey_templates.py | 1 处 | - | 已添加 |
| service/surveys.py | 3 处 | 3 处 | 已添加 |
| service/tickets/assignment.py | 1 处 | - | 已添加 |
| service/tickets/crud.py | 1 处 | - | 已添加 |
| service/tickets/issues.py | 1 处 | - | 已添加 |
| service/tickets/status.py | 2 处 | - | 已添加 |

### staff_matching 模块

| 文件 | 规则1 | 规则2 | import |
|------|-------|-------|--------|
| staff_matching/evaluations.py | 2 处 | - | 已添加 |
| staff_matching/profiles.py | 2 处 | - | 已添加 |
| staff_matching/staffing_needs.py | 3 处 | - | 已添加 |
| staff_matching/tags.py | 2 处 | 1 处 | 已添加 |

### standard_costs 模块

| 文件 | 规则1 | 规则2 | import |
|------|-------|-------|--------|
| standard_costs/crud.py | 3 处 | - | 已添加 |
| standard_costs/history.py | 2 处 | - | 已添加 |
| standard_costs/project_integration.py | 2 处 | - | 已添加 |

### task_center 模块

| 文件 | 规则1 | 规则2 | import |
|------|-------|-------|--------|
| task_center/batch_attributes.py | 1 处 | - | 已添加 |
| task_center/comments.py | 2 处 | - | 已添加 |
| task_center/complete.py | 1 处 | - | 已添加 |
| task_center/detail.py | 1 处 | - | 已添加 |
| task_center/reject.py | 2 处 | - | 已添加 |
| task_center/transfer.py | 1 处 | - | 已添加 |

### technical_review 模块

| 文件 | 规则1 | 规则2 | import |
|------|-------|-------|--------|
| technical_review/checklists.py | 2 处 | - | 已添加 |
| technical_review/issues.py | 2 处 | - | 已添加 |
| technical_review/participants.py | 3 处 | - | 已添加 |
| technical_review/reviews.py | 3 处 | - | 已添加 |

### users 模块

| 文件 | 规则1 | 规则2 | import |
|------|-------|-------|--------|
| users/crud_refactored.py | 5 处 | - | 已添加 |
| users/sync.py | 2 处 | - | 已添加 |
| users/time_allocation.py | 1 处 | - | 已添加 |

---

## 跳过文件说明

以下文件跳过（无匹配模式可替换）：

- `sales/ai_clarifications.py` - 无匹配模式
- `sales/contracts/*` - 已有 get_or_404 或使用复杂查询逻辑
- `sales/invoices/*` - detail 使用 f-string，无法安全替换
- `sales/opportunity_crud.py` - 无匹配模式
- `sales/payments/*` - 无匹配模式
- `sales/quote_*.py` - 无匹配模式
- `scheduler/*` - 无匹配模式
- `shortage/analytics/dashboard.py` - 无匹配模式
- `solution_credits/*` - 无匹配模式
- `staff_matching/matching.py`, `performance.py` - 无匹配模式
- `stage_templates.py` - 无匹配模式
- `task_center/create.py` - 无匹配模式
- `technical_review/materials.py` - 无匹配模式
- `technical_spec/*` - 无匹配模式
- `timesheet/records.py` - 无匹配模式
- `users/utils.py` - 无匹配模式

---

## 技术说明

### import 智能处理

- 文件无任何 db_helpers 导入 → 添加完整行 `from app.utils.db_helpers import get_or_404, save_obj, delete_obj`
- 文件已有部分导入（如仅 `get_or_404`）且需用 `save_obj` → 扩展现有导入行
- 只在顶层（无缩进）位置扫描导入，避免误识别函数体内的局部 import

### 已知限制（正确决策）

1. **f-string detail 不替换**: 如 `detail=f"项目不存在 (ID: {project_id})"` — 无法安全传给 `get_or_404`
2. **复杂过滤不替换**: 只替换 `.filter(Model.id == var).first()` 这一精确模式
3. **非连续 add/commit/refresh 不替换**: 中间有其他 `db.add()` 的批量操作不替换

---

*报告自动生成，E组代码去重任务完成。*
