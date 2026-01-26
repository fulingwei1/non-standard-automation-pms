# 项目中心CRUD路由基类迁移指南

> **创建日期**: 2026-01-24  
> **基于**: 里程碑模块迁移经验  
> **目标**: 将项目子模块的CRUD端点迁移到使用项目中心CRUD路由基类

---

## 一、迁移前准备

### 1.1 了解基类功能

项目中心CRUD路由基类（`create_project_crud_router`）自动提供以下功能：

| 功能 | 说明 | 端点 |
|------|------|------|
| 列表查询 | 支持分页、搜索、排序、筛选 | `GET /projects/{project_id}/resources/` |
| 创建 | 自动注入项目ID，权限检查 | `POST /projects/{project_id}/resources/` |
| 详情查询 | 自动项目ID过滤 | `GET /projects/{project_id}/resources/{id}` |
| 更新 | 自动项目ID过滤 | `PUT /projects/{project_id}/resources/{id}` |
| 删除 | 自动项目ID过滤 | `DELETE /projects/{project_id}/resources/{id}` |

### 1.2 检查现有代码

在迁移前，检查以下内容：

1. **模型字段**
   - ✅ 确认模型有 `project_id` 字段（或自定义字段名）
   - ✅ 确认字段类型为 `Integer` 或 `ForeignKey`

2. **Schema定义**
   - ✅ 确认有 `CreateSchema`、`UpdateSchema`、`ResponseSchema`
   - ⚠️ 如果 `CreateSchema` 中 `project_id` 是必需字段，需要改为可选

3. **权限配置**
   - ✅ 确认权限前缀（如 `milestone`、`cost`、`machine`）
   - ✅ 确认权限已配置（`milestone:read`、`milestone:create` 等）

4. **自定义端点**
   - ✅ 列出所有自定义端点（如 `complete`、`approve` 等）
   - ✅ 确认这些端点需要保留

### 1.3 备份代码

```bash
# 创建备份分支
git checkout -b backup/before-migration-{module-name}

# 提交当前代码
git add .
git commit -m "backup: 迁移前备份 {module-name} 模块"

# 切换回主分支
git checkout main
```

---

## 二、迁移步骤（详细）

### Step 1: 检查Schema定义

**问题**: `CreateSchema` 中的 `project_id` 字段通常是必需的，但路径中已经提供了。

**解决方案**: 将 `project_id` 改为可选字段。

**示例**:

```python
# 迁移前
class MilestoneCreate(BaseModel):
    project_id: int = Field(description="项目ID")
    milestone_name: str = Field(...)
    # ...

# 迁移后
class MilestoneCreate(BaseModel):
    project_id: Optional[int] = Field(None, description="项目ID（可选，通常从路径中获取）")
    milestone_name: str = Field(...)
    # ...
```

**文件位置**: `app/schemas/project/{module}.py`

---

### Step 2: 创建自定义筛选器（如需要）

如果模块需要自定义筛选（如状态筛选），创建筛选函数：

```python
# app/api/v1/endpoints/projects/{module}/crud.py

def filter_by_status(query, status: str):
    """自定义状态筛选器"""
    return query.filter(YourModel.status == status)

# 可以创建多个筛选器
def filter_by_type(query, type: str):
    """自定义类型筛选器"""
    return query.filter(YourModel.type == type)
```

**注意**: 
- 筛选函数接收 `query` 和筛选值，返回过滤后的 `query`
- 筛选值从 `request.query_params` 获取（基类自动处理）

---

### Step 3: 使用基类创建路由

**完整示例**:

```python
# -*- coding: utf-8 -*-
"""
项目{模块名} CRUD 操作（重构版本）

使用项目中心CRUD路由基类，大幅减少代码量
"""

from fastapi import APIRouter
from app.api.v1.core.project_crud_base import create_project_crud_router
from app.models.project import YourModel
from app.schemas.project import (
    YourModelCreate,
    YourModelUpdate,
    YourModelResponse
)

# 自定义筛选器（可选）
def filter_by_status(query, status: str):
    """自定义状态筛选器"""
    return query.filter(YourModel.status == status)

# 使用项目中心CRUD路由基类创建路由
router = create_project_crud_router(
    model=YourModel,
    create_schema=YourModelCreate,
    update_schema=YourModelUpdate,
    response_schema=YourModelResponse,
    permission_prefix="your_module",  # 如 "milestone", "cost", "machine"
    project_id_field="project_id",  # 如果字段名不同，修改这里
    keyword_fields=["name", "code", "description"],  # 关键词搜索字段
    default_order_by="created_at",  # 默认排序字段
    default_order_direction="desc",  # 默认排序方向
    custom_filters={
        "status": filter_by_status  # 自定义筛选器（可选）
    }
)
```

**参数说明**:

| 参数 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `model` | Type | ✅ | SQLAlchemy模型类 | `ProjectMilestone` |
| `create_schema` | Type | ✅ | 创建请求Schema | `MilestoneCreate` |
| `update_schema` | Type | ✅ | 更新请求Schema | `MilestoneUpdate` |
| `response_schema` | Type | ✅ | 响应Schema | `MilestoneResponse` |
| `permission_prefix` | str | ✅ | 权限前缀 | `"milestone"` |
| `project_id_field` | str | ❌ | 项目ID字段名 | `"project_id"` (默认) |
| `keyword_fields` | List[str] | ❌ | 关键词搜索字段 | `["name", "code"]` (默认) |
| `default_order_by` | str | ❌ | 默认排序字段 | `"created_at"` (默认) |
| `default_order_direction` | str | ❌ | 默认排序方向 | `"desc"` (默认) |
| `custom_filters` | Dict | ❌ | 自定义筛选器 | `{"status": filter_func}` |
| `before_create` | Callable | ❌ | 创建前钩子 | 见"高级用法" |
| `after_create` | Callable | ❌ | 创建后钩子 | 见"高级用法" |
| `before_update` | Callable | ❌ | 更新前钩子 | 见"高级用法" |
| `after_update` | Callable | ❌ | 更新后钩子 | 见"高级用法" |
| `before_delete` | Callable | ❌ | 删除前钩子 | 见"高级用法" |
| `after_delete` | Callable | ❌ | 删除后钩子 | 见"高级用法" |

---

### Step 4: 处理自定义端点

如果模块有自定义端点（如 `complete`、`approve`），需要单独实现：

```python
# app/api/v1/endpoints/projects/{module}/workflow.py

from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.models.project import YourModel
from app.models.user import User
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()

@router.put("/{item_id}/complete", response_model=YourModelResponse)
def complete_item(
    project_id: int = Path(..., description="项目ID"),
    item_id: int = Path(..., description="资源ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("your_module:update")),
):
    """完成资源（自定义端点）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    item = db.query(YourModel).filter(
        YourModel.id == item_id,
        YourModel.project_id == project_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="资源不存在")
    
    # 自定义逻辑
    item.status = "COMPLETED"
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return item
```

**注意**: 
- 自定义端点需要手动实现项目权限检查
- 自定义端点需要手动实现项目ID过滤
- 自定义端点需要手动实现404错误处理

---

### Step 5: 更新路由注册

在 `app/api/v1/endpoints/projects/__init__.py` 中注册路由：

```python
from .{module} import router as {module}_router

# 注册CRUD路由
router.include_router(
    {module}_router,
    prefix="/{project_id}/{module}",
    tags=["projects-{module}"],
)

# 如果有自定义端点，也需要注册
from .{module}.workflow import router as {module}_workflow_router
router.include_router(
    {module}_workflow_router,
    prefix="/{project_id}/{module}",
    tags=["projects-{module}"],
)
```

**注意**: 
- 路由顺序很重要！静态路径必须在动态路径之前
- 如果有多个路由文件，确保正确聚合

---

### Step 6: 移除旧代码

如果旧代码中有重复的端点（如删除端点），需要移除：

```python
# 旧代码（需要移除）
@router.delete("/{item_id}")
def delete_item(...):
    # ... 删除逻辑

# 新代码（由基类提供，无需实现）
# DELETE /projects/{project_id}/{module}/{item_id} 已由基类自动提供
```

**检查清单**:
- [ ] 移除重复的列表端点
- [ ] 移除重复的创建端点
- [ ] 移除重复的详情端点
- [ ] 移除重复的更新端点
- [ ] 移除重复的删除端点
- [ ] 保留自定义端点

---

### Step 7: 运行测试

```bash
# 运行模块测试
python3 -m pytest tests/api/test_{module}_api.py -v

# 运行集成测试
python3 -m pytest tests/integration/test_{module}_api.py -v

# 检查代码覆盖率
python3 -m pytest tests/api/test_{module}_api.py --cov=app.api.v1.endpoints.projects.{module} --cov-report=html
```

**测试检查清单**:
- [ ] 列表查询正常
- [ ] 分页功能正常
- [ ] 关键词搜索正常
- [ ] 排序功能正常
- [ ] 自定义筛选正常
- [ ] 创建功能正常
- [ ] 详情查询正常
- [ ] 更新功能正常
- [ ] 删除功能正常
- [ ] 自定义端点正常
- [ ] 权限检查正常
- [ ] 404错误处理正常

---

### Step 8: 验证功能

**手动测试清单**:

1. **列表查询**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/projects/1/{module}/?page=1&page_size=20&keyword=test&status=PENDING"
   ```

2. **创建**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/projects/1/{module}/" \
     -H "Content-Type: application/json" \
     -d '{"name": "测试", "code": "TEST001"}'
   ```

3. **详情查询**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/projects/1/{module}/1"
   ```

4. **更新**
   ```bash
   curl -X PUT "http://localhost:8000/api/v1/projects/1/{module}/1" \
     -H "Content-Type: application/json" \
     -d '{"name": "更新后的名称"}'
   ```

5. **删除**
   ```bash
   curl -X DELETE "http://localhost:8000/api/v1/projects/1/{module}/1"
   ```

6. **自定义端点**
   ```bash
   curl -X PUT "http://localhost:8000/api/v1/projects/1/{module}/1/complete"
   ```

---

## 三、常见问题和解决方案

### 问题1: Schema验证失败 - project_id字段必需

**错误信息**:
```
{"code":"VALIDATION_ERROR","message":"请求参数验证失败：project_id Field required"}
```

**原因**: `CreateSchema` 中 `project_id` 是必需字段，但路径中已经提供了。

**解决方案**: 将 `project_id` 改为可选字段。

```python
# 修复前
project_id: int = Field(description="项目ID")

# 修复后
project_id: Optional[int] = Field(None, description="项目ID（可选，通常从路径中获取）")
```

---

### 问题2: 自定义筛选参数不生效

**原因**: FastAPI不支持 `**kwargs` 接收查询参数，需要通过 `Request` 对象获取。

**解决方案**: 基类已自动处理，确保筛选函数正确实现：

```python
def filter_by_status(query, status: str):
    """自定义状态筛选器"""
    return query.filter(YourModel.status == status)

# 在创建路由时传入
custom_filters={
    "status": filter_by_status
}
```

**使用方式**: `GET /projects/{project_id}/{module}/?status=PENDING`

---

### 问题3: 权限检查失败

**错误信息**:
```
{"detail": "您没有权限访问该项目"}
```

**原因**: 
1. 用户没有项目访问权限
2. 权限前缀配置错误

**解决方案**:
1. 检查用户是否有项目访问权限
2. 确认 `permission_prefix` 配置正确
3. 确认权限已配置（如 `milestone:read`、`milestone:create` 等）

---

### 问题4: 404错误 - 资源不存在

**原因**: 
1. 资源ID不存在
2. 资源不属于该项目

**解决方案**: 基类已自动处理，确保：
1. 资源ID正确
2. 资源确实属于该项目
3. 项目ID正确

---

### 问题5: 删除端点返回204但期望200

**原因**: HTTP 204状态码不能有响应体。

**解决方案**: 基类已正确处理，返回204状态码，无响应体。

**如果需要响应体**: 可以修改基类或使用钩子函数。

---

### 问题6: 自定义端点与基类端点冲突

**原因**: 路由路径冲突。

**解决方案**: 
1. 确保自定义端点路径更具体（如 `/complete`）
2. 确保自定义端点在基类路由之后注册
3. 使用不同的HTTP方法（如 `PUT` vs `DELETE`）

---

## 四、最佳实践

### 4.1 Schema设计

1. **project_id字段**
   - ✅ 在 `CreateSchema` 中设为可选
   - ✅ 在 `UpdateSchema` 中不包含（不允许修改）
   - ✅ 在 `ResponseSchema` 中包含（返回时显示）

2. **字段验证**
   - ✅ 使用 `Field` 添加验证规则
   - ✅ 使用 `Optional` 标记可选字段
   - ✅ 使用 `max_length` 限制字符串长度

### 4.2 筛选器设计

1. **命名规范**
   - ✅ 使用 `filter_by_{field_name}` 命名
   - ✅ 函数接收 `query` 和筛选值
   - ✅ 返回过滤后的 `query`

2. **类型安全**
   - ✅ 添加类型提示
   - ✅ 处理类型转换（如字符串转整数）

### 4.3 自定义端点设计

1. **路径设计**
   - ✅ 使用动词命名（如 `complete`、`approve`、`cancel`）
   - ✅ 使用 `PUT` 方法（表示状态变更）
   - ✅ 避免与CRUD端点冲突

2. **权限检查**
   - ✅ 使用 `check_project_access_or_raise` 检查项目权限
   - ✅ 使用 `require_permission` 检查操作权限
   - ✅ 在函数开始处检查，尽早失败

### 4.4 错误处理

1. **404错误**
   - ✅ 基类已自动处理
   - ✅ 自定义端点需要手动处理

2. **权限错误**
   - ✅ 基类已自动处理
   - ✅ 自定义端点需要手动处理

3. **验证错误**
   - ✅ FastAPI自动处理
   - ✅ 确保Schema定义正确

---

## 五、高级用法

### 5.1 使用钩子函数

钩子函数允许在CRUD操作前后执行自定义逻辑：

```python
def before_create_hook(item_data: dict, project_id: int, current_user: User) -> dict:
    """创建前钩子"""
    # 可以修改创建数据
    item_data["created_by"] = current_user.id
    item_data["status"] = "PENDING"  # 设置默认状态
    return item_data

def after_create_hook(item_id: int, project_id: int, current_user: User):
    """创建后钩子"""
    # 可以执行后续操作，如发送通知
    logger.info(f"用户 {current_user.id} 在项目 {project_id} 中创建了资源 {item_id}")

router = create_project_crud_router(
    # ... 其他参数
    before_create=before_create_hook,
    after_create=after_create_hook,
)
```

**钩子函数类型**:

| 钩子 | 签名 | 说明 |
|------|------|------|
| `before_create` | `(item_data: dict, project_id: int, current_user: User) -> dict` | 创建前，可以修改数据 |
| `after_create` | `(item_id: int, project_id: int, current_user: User) -> None` | 创建后，可以执行后续操作 |
| `before_update` | `(item, update_data: dict, project_id: int, current_user: User) -> bool` | 更新前，返回False可取消更新 |
| `after_update` | `(item_id: int, project_id: int, current_user: User) -> None` | 更新后，可以执行后续操作 |
| `before_delete` | `(item, project_id: int, current_user: User) -> bool` | 删除前，返回False可取消删除 |
| `after_delete` | `(item_id: int, project_id: int, current_user: User) -> None` | 删除后，可以执行后续操作 |

---

### 5.2 多字段筛选

如果需要多个筛选字段，创建多个筛选函数：

```python
def filter_by_status(query, status: str):
    return query.filter(YourModel.status == status)

def filter_by_type(query, type: str):
    return query.filter(YourModel.type == type)

def filter_by_owner(query, owner_id: str):
    return query.filter(YourModel.owner_id == int(owner_id))

router = create_project_crud_router(
    # ... 其他参数
    custom_filters={
        "status": filter_by_status,
        "type": filter_by_type,
        "owner_id": filter_by_owner,
    }
)
```

**使用方式**: `GET /projects/{project_id}/{module}/?status=PENDING&type=TYPE1&owner_id=1`

---

### 5.3 复杂筛选逻辑

如果需要复杂的筛选逻辑（如范围查询），在筛选函数中处理：

```python
def filter_by_date_range(query, date_range: str):
    """日期范围筛选，格式: YYYY-MM-DD,YYYY-MM-DD"""
    try:
        start_str, end_str = date_range.split(",")
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        return query.filter(
            YourModel.created_at >= start_date,
            YourModel.created_at <= end_date
        )
    except (ValueError, AttributeError):
        return query  # 解析失败时返回原查询

router = create_project_crud_router(
    # ... 其他参数
    custom_filters={
        "date_range": filter_by_date_range,
    }
)
```

---

## 六、迁移检查清单

### 迁移前

- [ ] 备份代码（创建备份分支）
- [ ] 检查模型字段（确认有 `project_id` 字段）
- [ ] 检查Schema定义（确认有Create/Update/Response Schema）
- [ ] 检查权限配置（确认权限已配置）
- [ ] 列出自定义端点（确认需要保留的端点）

### 迁移中

- [ ] 修改Schema（将 `project_id` 改为可选）
- [ ] 创建自定义筛选器（如需要）
- [ ] 使用基类创建路由
- [ ] 处理自定义端点
- [ ] 更新路由注册
- [ ] 移除旧代码

### 迁移后

- [ ] 运行测试（单元测试、集成测试）
- [ ] 验证功能（手动测试所有端点）
- [ ] 检查代码行数（对比迁移前后）
- [ ] 更新文档（API文档、开发指南）
- [ ] 提交代码（使用清晰的commit message）

---

## 七、代码对比示例

### 迁移前（126行）

```python
@router.get("/", response_model=List[MilestoneResponse])
def read_project_milestones(
    project_id: int = Path(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:read")),
):
    check_project_access_or_raise(db, current_user, project_id)
    milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id
    ).all()
    return milestones

@router.post("/", response_model=MilestoneResponse)
def create_project_milestone(
    project_id: int = Path(...),
    milestone_in: MilestoneCreate = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:create")),
):
    check_project_access_or_raise(db, current_user, project_id)
    milestone = ProjectMilestone(**milestone_in.model_dump(), project_id=project_id)
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone

# ... 其他3个端点类似，每个20-30行
```

### 迁移后（42行）

```python
def filter_by_status(query, status: str):
    return query.filter(ProjectMilestone.status == status)

router = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
    project_id_field="project_id",
    keyword_fields=["milestone_name", "milestone_code", "description"],
    default_order_by="planned_date",
    default_order_direction="desc",
    custom_filters={"status": filter_by_status}
)
```

**代码减少**: 从126行 → 42行，减少67%

---

## 八、FAQ

### Q1: 基类支持哪些功能？

**A**: 基类支持：
- ✅ 标准CRUD操作（列表、创建、详情、更新、删除）
- ✅ 分页支持
- ✅ 关键词搜索
- ✅ 排序支持
- ✅ 自定义筛选
- ✅ 权限检查
- ✅ 项目ID过滤
- ✅ 钩子函数

### Q2: 如何添加自定义端点？

**A**: 在单独的文件中实现（如 `workflow.py`），然后注册到主路由。

### Q3: 如何处理复杂的业务逻辑？

**A**: 使用钩子函数（`before_create`、`after_create` 等）或创建Service层。

### Q4: 如何迁移已有的大量数据？

**A**: 迁移不影响数据，只是改变API端点路径。前端需要更新API调用。

### Q5: 性能会受影响吗？

**A**: 不会。基类使用相同的数据库查询，性能相同或更好（因为代码更简洁）。

### Q6: 如何回滚迁移？

**A**: 使用git回滚到备份分支，或手动恢复旧代码。

---

## 九、参考资源

### 文档

- [项目中心CRUD路由基类使用指南](./project-crud-router-guide.md)
- [同步CRUD基类快速启动指南](../app/common/crud/SYNC_QUICK_START.md)
- [渐进式重构实施计划](../plans/gradual-refactoring-implementation-plan.md)

### 示例代码

- [里程碑模块迁移示例](../../app/api/v1/endpoints/projects/milestones/crud.py)
- [基类实现](../../app/api/v1/core/project_crud_base.py)
- [测试示例](../../tests/api/test_project_milestones_api.py)

### 相关报告

- [里程碑模块迁移最终报告](../reports/milestone-migration-final-report.md)
- [测试验证报告](../reports/milestone-migration-test-validation.md)

---

## 十、总结

### 迁移收益

- ✅ **代码减少60%+** - 从平均150行 → 50行
- ✅ **功能增强** - 自动获得分页、搜索、排序功能
- ✅ **统一代码模式** - 所有模块使用相同的基类
- ✅ **易于维护** - 修复一处，所有地方受益
- ✅ **易于测试** - 基类已测试，只需测试业务逻辑

### 迁移时间

- **简单模块**（如机器、成员）: 1-2小时
- **中等模块**（如成本、里程碑）: 2-3小时
- **复杂模块**（有大量自定义逻辑）: 3-4小时

### 下一步

完成迁移后，可以：
1. 继续迁移其他模块
2. 优化和完善基类
3. 更新前端API调用
4. 废弃全局API端点

---

**文档版本**: v1.0  
**创建日期**: 2026-01-24  
**最后更新**: 2026-01-24  
**状态**: ✅ 基于里程碑模块迁移经验，已验证可用
