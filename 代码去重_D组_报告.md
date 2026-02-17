# 代码去重 D组 报告

**执行时间**: 2026-02-17  
**覆盖范围**: projects, purchase, qualification, rd_project, report_center 等模块  
**Commit**: `refactor(D-group): 使用 db_helpers 消除 projects/purchase/sales 重复代码`

---

## 执行摘要

| 指标 | 数量 |
|------|------|
| 处理文件数 | 47 |
| 实际修改文件数 | 9 |
| 无需修改（无匹配模式） | 38 |
| Pattern1 替换次数（query+404） | 15 |
| Pattern2 替换次数（save_obj） | 0 |
| 语法错误/回滚 | 0 |

---

## 修改文件明细

| 文件 | Pattern1 | Pattern2 | import 新增 |
|------|----------|----------|------------|
| `app/api/v1/endpoints/project_contributions.py` | 1 | 0 | ✅ |
| `app/api/v1/endpoints/project_review/lessons.py` | 2 | 0 | ✅ |
| `app/api/v1/endpoints/project_review/reviews.py` | 3 | 0 | ✅ |
| `app/api/v1/endpoints/project_workspace.py` | 1 | 0 | ✅ |
| `app/api/v1/endpoints/qualification/levels.py` | 3 | 0 | ✅ |
| `app/api/v1/endpoints/qualification/models.py` | 2 | 0 | ✅ |
| `app/api/v1/endpoints/report_center/generate/download.py` | 1 | 0 | ✅ |
| `app/api/v1/endpoints/report_center/generate/export.py` | 1 | 0 | ✅ |
| `app/api/v1/endpoints/report_center/templates.py` | 1 | 0 | ✅ |

---

## Pattern1 替换示例

### Before
```python
project = db.query(Project).filter(Project.id == project_id).first()
if not project:
    raise HTTPException(status_code=404, detail="项目不存在")
```

### After
```python
project = get_or_404(db, Project, project_id, "项目不存在")
```

---

## Pattern2 未触发原因

D组文件中的 `db.add + db.commit + db.refresh` 后均跟随 `return ResponseModel(...)` 或继续业务逻辑，而非直接 `return obj`，因此不符合 Pattern2 的替换条件（要求4行连续: `db.add(obj) → db.commit() → db.refresh(obj) → return obj`）。

这属于预期行为，保持原有结构更安全。

---

## 跳过说明

以下 38 个文件未发现可替换的明确模式（均跳过）：

- `project_review/comparison.py`, `project_review/knowledge.py`
- `projects/approvals/action_new.py`, `projects/approvals/cancel_new.py`
- `projects/costs/allocation.py`, `projects/costs/analysis.py`, `projects/costs/forecast.py`
- `projects/evaluations/crud.py`, `projects/evaluations/custom.py`
- `projects/ext_best_practices.py`, `projects/ext_reviews.py`
- `projects/machines/crud.py`, `projects/machines/custom.py`
- `projects/members/crud.py`
- `projects/milestones/crud.py`, `projects/milestones/workflow.py`
- `projects/progress/summary.py`
- `projects/project_crud.py`
- `projects/resource_plan/assignment.py`, `projects/resource_plan/crud.py`
- `projects/risks.py`
- `projects/roles/leads.py`, `projects/roles/team_members.py`
- `projects/schedule_prediction.py`
- `projects/stages/crud.py`, `projects/stages/node_operations.py`, `projects/stages/stage_operations.py`, `projects/stages/status_updates.py`
- `projects/template_versions.py`
- `projects/timesheet/crud.py`
- `purchase/orders_refactored.py`, `purchase/receipts.py`, `purchase/requests_refactored.py`
- `purchase_intelligence.py`
- `qualification/assessments.py`, `qualification/employees.py`
- `rd_project/documents.py`, `rd_project/expenses.py`
- `report_center/generate/download.py`（已在此次处理）

> 注：这些文件可能使用了多条件 `.filter()`（如额外的状态过滤），或未使用简单的 query+404 模式，均属于正常业务逻辑，按规则跳过。

---

## 质量保证

- 每个文件修改后执行 `ast.parse()` 语法检查
- 发生语法错误时自动回滚（本次0个回滚）
- 仅替换单条件 `.filter(Model.field == id)` 的明确模式
- 多条件过滤（含逗号）一律跳过，避免破坏业务语义
