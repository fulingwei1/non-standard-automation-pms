# 代码去重 A组 - 处理报告

**任务**: 将 acceptance / alerts / analytics / approvals / assembly_kit 模块中的重复模式替换为 db_helpers 工具函数

**完成时间**: 2026-02-17

---

## 处理范围

共处理以下 5 个模块的 35 个文件：

| 模块 | 文件数 |
|------|--------|
| acceptance | 18 |
| alerts | 6 |
| analytics | 1 |
| approvals | 1 |
| assembly_kit | 9 |

---

## 替换统计

| 替换类型 | 数量 |
|----------|------|
| `get_or_404` 替换（查询+404模式） | 67 处 |
| `save_obj` 替换（add+commit+refresh+return） | 3 处 |
| 新增 `db_helpers` import 的文件 | 25 个 |

当前 A 组文件中 db_helpers 函数使用情况（最终状态）：
- `get_or_404` 调用: 115 处
- `save_obj` 调用: 6 处
- 带 db_helpers import 的文件: 30 个

---

## 替换示例

### 规则2: get_or_404 替换

**替换前:**
```python
order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
if not order:
    raise HTTPException(status_code=404, detail="验收单不存在")
```

**替换后:**
```python
order = get_or_404(db, AcceptanceOrder, order_id, "验收单不存在")
```

### 规则3: save_obj 替换 (alerts/rules.py)

**替换前:**
```python
db.add(rule)
db.commit()
db.refresh(rule)

return rule
```

**替换后:**
```python
return save_obj(db, rule)
```

---

## 跳过的文件（无匹配模式）

以下文件中无法安全替换的原因：

| 文件 | 原因 |
|------|------|
| `presale_ai_emotion.py` | 查询使用非 id 字段过滤，或查询结果不直接用于 404 |
| `ai_planning.py` | 同上 |
| `_shared/unified_reports.py` | 无数据库查询 |
| `alerts/exports.py` | 无 get_or_404 模式 |
| `alerts/notifications.py` | 无 get_or_404 模式 |
| `alerts/subscriptions.py` | 多条件过滤（id + user_id），无法用 get_or_404 替换 |
| `analytics/resource_conflicts.py` | 多条件过滤，无法用 get_or_404 替换 |
| `approvals/pending_refactored.py` | 无 get_or_404 模式 |
| `assembly_kit/material_mapping.py` | 无匹配的单字段 id 过滤模式 |
| `assembly_kit/stages.py` | 按 stage_code 过滤（非 id 字段） |

---

## 质量验证

- **语法检查**: 所有 25 个修改文件均通过 `ast.parse()` 语法检查 ✅
- **服务器启动**: `uvicorn app.main:app` 启动无 ERROR ✅
- **import 位置**: 所有 db_helpers import 均正确插入到文件顶部 import 区域 ✅

---

## 注意事项

1. 多条件过滤查询（如 `filter(Model.id == x, Model.user_id == y).first()`）未替换，因为 `get_or_404` 只支持单字段 id 过滤
2. 按非 id 字段过滤的查询未替换
3. `db.add + db.commit + db.refresh` 后跟随非直接 `return obj` 的模式未替换（如 `return build_issue_response(issue, db)`）

---

## Git Commit

```
refactor(A-group): 使用 db_helpers 消除 acceptance/alerts/analytics/approvals/assembly_kit 重复代码
```

Commit hash: `bface01e`
