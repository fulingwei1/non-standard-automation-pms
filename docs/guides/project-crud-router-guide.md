# 项目中心CRUD路由基类使用指南

> **适用场景**: 快速创建项目子模块的CRUD端点，减少重复代码

---

## 一、快速开始（5分钟）

### 1.1 最简单的使用方式

```python
from app.api.v1.core.project_crud_base import create_project_crud_router
from app.models.project import ProjectMilestone
from app.schemas.project import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse
)

# 创建路由
milestone_router = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
    project_id_field="project_id"
)

# 在主路由中注册
from fastapi import APIRouter
router = APIRouter()
router.include_router(
    milestone_router,
    prefix="/{project_id}/milestones",
    tags=["projects-milestones"]
)
```

**就这么简单！** 自动获得以下5个端点：

- `GET /projects/{project_id}/milestones/` - 列表查询
- `POST /projects/{project_id}/milestones/` - 创建
- `GET /projects/{project_id}/milestones/{milestone_id}` - 详情
- `PUT /projects/{project_id}/milestones/{milestone_id}` - 更新
- `DELETE /projects/{project_id}/milestones/{milestone_id}` - 删除

---

## 二、核心功能

### 2.1 自动功能

| 功能 | 说明 |
|------|------|
| 项目权限检查 | 自动检查用户是否有权限访问该项目 |
| 项目ID过滤 | 自动过滤只返回属于该项目的资源 |
| 项目ID注入 | 创建时自动使用路径中的项目ID |
| 分页支持 | 自动支持分页查询 |
| 关键词搜索 | 支持关键词搜索（可配置字段） |
| 排序支持 | 支持自定义排序 |
| 权限控制 | 自动检查CRUD权限 |

### 2.2 列表查询功能

**支持的查询参数**:

- `page` - 页码（默认1）
- `page_size` - 每页数量（默认100，最大100）
- `keyword` - 关键词搜索
- `order_by` - 排序字段
- `order_direction` - 排序方向（asc/desc）

**示例**:
```
GET /projects/1/milestones/?page=1&page_size=20&keyword=测试&order_by=planned_date&order_direction=desc
```

---

## 三、高级用法

### 3.1 自定义关键词搜索字段

```python
milestone_router = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
    keyword_fields=["milestone_name", "description", "code"]  # 自定义搜索字段
)
```

### 3.2 自定义默认排序

```python
milestone_router = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
    default_order_by="planned_date",  # 默认按计划日期排序
    default_order_direction="desc"     # 降序
)
```

### 3.3 自定义筛选器

```python
def filter_by_status(query, status: str):
    """自定义状态筛选器"""
    return query.filter(ProjectMilestone.status == status)

milestone_router = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
    custom_filters={
        "status": filter_by_status  # 在列表接口中可以通过 ?status=ACTIVE 筛选
    }
)
```

### 3.4 钩子函数

```python
def before_create_milestone(item_data: dict, project_id: int, current_user):
    """创建前钩子：自动设置默认值"""
    # 例如：自动生成编码
    if "code" not in item_data or not item_data["code"]:
        item_data["code"] = f"MIL-{project_id}-{len(item_data)}"
    
    # 例如：设置创建人
    if "created_by" not in item_data:
        item_data["created_by"] = current_user.id
    
    return item_data


def after_create_milestone(db_item, project_id: int, current_user):
    """创建后钩子：发送通知等"""
    # 例如：发送通知
    # send_notification(f"创建了里程碑: {db_item.milestone_name}")
    return db_item


def before_update_milestone(item, item_in, project_id: int, current_user):
    """更新前钩子：验证业务规则"""
    # 例如：检查是否可以更新
    if item.status == "COMPLETED":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已完成的里程碑不能修改"
        )
    return item_in


def after_update_milestone(item, project_id: int, current_user):
    """更新后钩子：记录变更历史"""
    # 例如：记录变更历史
    # log_change("milestone_updated", item.id, current_user.id)
    return item


def before_delete_milestone(item, project_id: int, current_user):
    """删除前钩子：检查是否可以删除"""
    # 例如：检查是否可以删除
    if item.status == "COMPLETED":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已完成的里程碑不能删除"
        )
    return True  # 返回True允许删除，False取消删除


def after_delete_milestone(item_id: int, project_id: int, current_user):
    """删除后钩子：清理关联数据"""
    # 例如：清理关联数据
    # cleanup_related_data(item_id)
    pass


milestone_router = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
    before_create=before_create_milestone,
    after_create=after_create_milestone,
    before_update=before_update_milestone,
    after_update=after_update_milestone,
    before_delete=before_delete_milestone,
    after_delete=after_delete_milestone,
)
```

---

## 四、添加自定义端点

如果需要添加自定义端点（如完成里程碑、取消里程碑等），可以在创建路由后添加：

```python
# 创建基础路由
milestone_router = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone"
)

# 添加自定义端点
@milestone_router.put("/{item_id}/complete", response_model=MilestoneResponse)
def complete_milestone(
    project_id: int = Path(..., description="项目ID"),
    item_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:update")),
):
    """完成里程碑（自定义端点）"""
    from app.api import deps
    from app.core import security
    from app.utils.permission_helpers import check_project_access_or_raise
    from fastapi import Path, Depends, HTTPException, status
    
    check_project_access_or_raise(db, current_user, project_id)
    
    milestone = db.query(ProjectMilestone).filter(
        ProjectMilestone.id == item_id,
        ProjectMilestone.project_id == project_id
    ).first()
    
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="里程碑不存在"
        )
    
    milestone.status = "COMPLETED"
    db.commit()
    db.refresh(milestone)
    
    return MilestoneResponse.model_validate(milestone)
```

---

## 五、完整示例

### 5.1 里程碑模块完整示例

```python
# app/api/v1/endpoints/projects/milestones/router.py

from fastapi import APIRouter, Path, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.core.project_crud_base import create_project_crud_router
from app.api import deps
from app.core import security
from app.models.project import ProjectMilestone
from app.models.user import User
from app.schemas.project import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse
)

# 创建基础CRUD路由
router = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
    project_id_field="project_id",
    keyword_fields=["milestone_name", "description"],
    default_order_by="planned_date",
    default_order_direction="desc"
)

# 添加自定义端点：完成里程碑
@router.put("/{item_id}/complete", response_model=MilestoneResponse)
def complete_milestone(
    project_id: int = Path(..., description="项目ID"),
    item_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:update")),
):
    """完成里程碑"""
    from app.utils.permission_helpers import check_project_access_or_raise
    
    check_project_access_or_raise(db, current_user, project_id)
    
    milestone = db.query(ProjectMilestone).filter(
        ProjectMilestone.id == item_id,
        ProjectMilestone.project_id == project_id
    ).first()
    
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="里程碑不存在"
        )
    
    if milestone.status == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="里程碑已完成"
        )
    
    milestone.status = "COMPLETED"
    db.commit()
    db.refresh(milestone)
    
    return MilestoneResponse.model_validate(milestone)
```

### 5.2 在主路由中注册

```python
# app/api/v1/endpoints/projects/__init__.py

from fastapi import APIRouter
from .milestones.router import router as milestones_router

router = APIRouter()

# 注册里程碑路由
router.include_router(
    milestones_router,
    prefix="/{project_id}/milestones",
    tags=["projects-milestones"]
)
```

---

## 六、参数说明

### 6.1 必需参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `model` | Type[ModelType] | SQLAlchemy模型类 |
| `create_schema` | Type[CreateSchemaType] | 创建请求Schema |
| `update_schema` | Type[UpdateSchemaType] | 更新请求Schema |
| `response_schema` | Type[ResponseSchemaType] | 响应Schema |
| `permission_prefix` | str | 权限前缀，如 "milestone" 会生成 "milestone:read" 等 |

### 6.2 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `project_id_field` | str | "project_id" | 项目ID字段名 |
| `keyword_fields` | List[str] | ["name", "code"] | 关键词搜索字段列表 |
| `default_order_by` | str | "created_at" | 默认排序字段 |
| `default_order_direction` | str | "desc" | 默认排序方向 |
| `custom_filters` | Dict[str, Callable] | None | 自定义筛选器字典 |
| `before_create` | Callable | None | 创建前钩子函数 |
| `after_create` | Callable | None | 创建后钩子函数 |
| `before_update` | Callable | None | 更新前钩子函数 |
| `after_update` | Callable | None | 更新后钩子函数 |
| `before_delete` | Callable | None | 删除前钩子函数 |
| `after_delete` | Callable | None | 删除后钩子函数 |

---

## 七、钩子函数签名

### 7.1 创建钩子

```python
def before_create(item_data: dict, project_id: int, current_user: User) -> dict:
    """创建前钩子"""
    # 可以修改 item_data
    return item_data

def after_create(db_item: ModelType, project_id: int, current_user: User) -> ModelType:
    """创建后钩子"""
    # 可以修改 db_item，需要返回修改后的对象
    return db_item
```

### 7.2 更新钩子

```python
def before_update(item: ModelType, item_in: UpdateSchemaType, project_id: int, current_user: User) -> UpdateSchemaType:
    """更新前钩子"""
    # 可以修改 item_in 或验证业务规则
    # 如果返回 None，更新将被取消
    return item_in

def after_update(item: ModelType, project_id: int, current_user: User) -> ModelType:
    """更新后钩子"""
    # 可以修改 item，需要返回修改后的对象
    return item
```

### 7.3 删除钩子

```python
def before_delete(item: ModelType, project_id: int, current_user: User) -> bool:
    """删除前钩子"""
    # 返回 True 允许删除，False 取消删除
    # 也可以抛出异常来阻止删除
    return True

def after_delete(item_id: int, project_id: int, current_user: User) -> None:
    """删除后钩子"""
    # 可以执行清理操作
    pass
```

---

## 八、对比：使用基类 vs 手动实现

### 8.1 代码量对比

| 方式 | 代码行数 | 说明 |
|------|----------|------|
| 手动实现 | ~150行 | 需要实现5个端点 |
| 使用基类 | ~20行 | 只需配置参数 |

**减少**: 87%的代码量

### 8.2 功能对比

| 功能 | 手动实现 | 使用基类 |
|------|----------|----------|
| 标准CRUD | ✅ | ✅ |
| 项目权限检查 | 需要手动实现 | ✅ 自动 |
| 项目ID过滤 | 需要手动实现 | ✅ 自动 |
| 分页支持 | 需要手动实现 | ✅ 自动 |
| 关键词搜索 | 需要手动实现 | ✅ 自动 |
| 排序支持 | 需要手动实现 | ✅ 自动 |
| 权限控制 | 需要手动实现 | ✅ 自动 |
| 钩子函数 | 需要手动实现 | ✅ 支持 |

---

## 九、最佳实践

### 9.1 权限前缀命名

- 使用资源名称作为前缀，如 `milestone`、`cost`、`machine`
- 权限会自动生成：`{prefix}:read`、`{prefix}:create`、`{prefix}:update`、`{prefix}:delete`

### 9.2 钩子函数使用

- **创建前钩子**: 用于设置默认值、生成编码等
- **创建后钩子**: 用于发送通知、记录日志等
- **更新前钩子**: 用于验证业务规则、检查状态等
- **更新后钩子**: 用于记录变更历史等
- **删除前钩子**: 用于检查是否可以删除
- **删除后钩子**: 用于清理关联数据

### 9.3 自定义端点

- 对于简单的自定义操作，可以直接在路由上添加端点
- 对于复杂的业务逻辑，建议创建独立的Service层

---

## 十、常见问题

### Q1: 如何修改项目ID字段名？

**A**: 使用 `project_id_field` 参数：

```python
router = create_project_crud_router(
    ...
    project_id_field="project_id"  # 修改为你的字段名
)
```

### Q2: 如何添加额外的查询参数？

**A**: 使用 `custom_filters` 参数：

```python
def filter_by_status(query, status: str):
    return query.filter(Model.status == status)

router = create_project_crud_router(
    ...
    custom_filters={"status": filter_by_status}
)
```

### Q3: 如何禁用某些端点？

**A**: 目前不支持禁用单个端点，但可以通过权限控制。如果需要完全禁用，建议手动实现路由。

### Q4: 如何处理复杂的业务逻辑？

**A**: 使用钩子函数或创建独立的Service层，在钩子函数中调用Service。

---

## 十一、完整示例代码

查看 `app/api/v1/core/project_crud_example.py` 获取更多完整示例。

---

**文档版本**: v1.0  
**最后更新**: 2026-01-24
