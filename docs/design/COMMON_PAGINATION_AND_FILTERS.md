# 通用分页与查询过滤使用说明

统一使用 `app.common.pagination` 与 `app.common.query_filters`，替代手写 `offset = (page - 1) * page_size` 和 `.like('%keyword%')`。

---

## 迁移步骤（现有代码如何改）

### 场景 A：列表接口（数据库分页）

**改前：**
```python
@router.get("/list")
def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Model).filter(...)
    if keyword:
        query = query.filter(Model.name.like(f"%{keyword}%"))
    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(...).offset(offset).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}
```

**改后：**
```python
from app.common.pagination import get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination

@router.get("/list")
def list_items(
    pagination=Depends(get_pagination_query),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Model).filter(...)
    query = apply_keyword_filter(query, Model, keyword, ["name"])  # 多字段可写 ["name", "code"]
    total = query.count()
    query = query.order_by(...)
    query = apply_pagination(query, pagination.offset, pagination.limit)
    items = query.all()
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pagination.pages_for_total(total),
    }
```

**迁移清单（场景 A）：**
1. 删除端点参数里的 `page`、`page_size`，改为 `pagination=Depends(get_pagination_query)`。
2. 删除 `offset = (page - 1) * page_size`，改用 `pagination.offset`、`pagination.limit`。
3. 若有关键词：把 `if keyword: query = query.filter(...like(...))` 换成 `query = apply_keyword_filter(query, Model, keyword, ["字段1", "字段2"])`。
4. 把 `.offset(offset).limit(page_size)` 换成 `query = apply_pagination(query, pagination.offset, pagination.limit)` 再 `.all()`。
5. 响应里用 `pagination.page`、`pagination.page_size`、`pagination.pages_for_total(total)`。

---

### 场景 B：列表接口（内存列表分页，先查全量再切片）

**改前：**
```python
tasks = engine.get_pending_tasks(...)  # 返回 list
total = len(tasks)
offset = (page - 1) * page_size
paginated_tasks = tasks[offset : offset + page_size]
return {"items": ..., "total": total, "page": page, "page_size": page_size, "pages": ...}
```

**改后：**
```python
pagination=Depends(get_pagination_query)
tasks = engine.get_pending_tasks(...)
total = len(tasks)
start, end = pagination.offset, pagination.offset + pagination.limit
paginated_tasks = tasks[start:end]
return {"items": ..., "total": total, "page": pagination.page, "page_size": pagination.page_size, "pages": pagination.pages_for_total(total)}
```

---

### 如何查找待迁移的代码

- 分页：在 `app/` 下搜索 `offset = (page - 1) * page_size` 或 `(page - 1) * page_size`。
- 关键词：搜索 `.like(` 或 `ilike(` 配合 `%` 的写法，改为 `apply_keyword_filter`。

---

## 1. 分页（pagination）

### 从 Query 参数解析

```python
from fastapi import Depends
from app.common.pagination import get_pagination_query, apply_pagination, PaginationParams

@router.get("/list")
def list_items(
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(get_db),
):
    query = db.query(Model).filter(...)
    total = query.count()
    query = query.order_by(Model.id.desc())
    query = apply_pagination(query, pagination.offset, pagination.limit)
    items = query.all()
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pagination.pages_for_total(total),
    }
```

### 内存列表分页

```python
from app.common.pagination import get_pagination_query

# 已有列表 tasks，按页切片
total = len(tasks)
start = pagination.offset
end = start + pagination.limit
page_items = tasks[start:end]
# 响应用 pagination.page, pagination.page_size, pagination.pages_for_total(total)
```

### 默认与上限

- 默认每页条数、上限从 `app.core.config.settings` 读取（`DEFAULT_PAGE_SIZE`、`MAX_PAGE_SIZE`）。
- `get_pagination_query` 的 Query 不传 `page_size` 时使用默认值。

## 2. 关键词过滤（query_filters）

### 对已有 Query 应用关键词

```python
from app.common.query_filters import apply_keyword_filter

query = db.query(Project).filter(Project.is_active == True)
query = apply_keyword_filter(query, Project, keyword, ["name", "code"])
# keyword 为 None 或空字符串时不做任何过滤
```

### 组合分页与关键词

```python
pagination = Depends(get_pagination_query)
query = db.query(Model).filter(...)
query = apply_keyword_filter(query, Model, keyword, ["name", "code"])
total = query.count()
query = apply_pagination(query, pagination.offset, pagination.limit)
items = query.all()
```

## 3. 迁移清单

已改为使用通用分页/过滤的端点示例：

- `app/api/v1/endpoints/timesheet/records.py` — list_timesheets
- `app/api/v1/endpoints/my/__init__.py` — get_my_timesheets, get_my_tasks, get_my_work_logs
- `app/api/v1/endpoints/projects/timesheet/crud.py` — list_project_timesheets
- `app/api/v1/endpoints/acceptance/order_approval.py` — get_pending_approval_tasks

其余端点可按相同模式逐步替换。
