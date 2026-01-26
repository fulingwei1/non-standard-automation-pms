# 同步版本CRUD基类快速开始指南

> **适用场景**: 当前项目使用同步Session，需要快速减少重复代码

---

## 一、推荐：BaseCRUDService + QueryParams（新）

> ✅ 默认集成分页/筛选/搜索/排序  
> ✅ 自动转换为响应Schema  
> ✅ 支持统一的钩子、批量操作、软删除

### 1.1 定义Service（仅需继承 + 声明字段）

```python
from sqlalchemy.orm import Session

from app.common.crud import BaseCRUDService
from app.models.project import ProjectMilestone
from app.schemas.project import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse,
)


class MilestoneService(
    BaseCRUDService[ProjectMilestone, MilestoneCreate, MilestoneUpdate, MilestoneResponse]
):
    """推荐用法：所有CRUD服务继承该基类"""

    # 声明一次即可，全局复用
    search_fields = ("milestone_name", "description")
    allowed_sort_fields = ("planned_date", "created_at")
    default_sort_field = "planned_date"
    unique_fields = ("milestone_code",)

    def __init__(self, db: Session):
        super().__init__(
            model=ProjectMilestone,
            db=db,
            response_schema=MilestoneResponse,
            resource_name="里程碑",
            default_filters={"is_archived": False},
        )
```

### 1.2 API层直接复用 QueryParams

```python
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.common.crud import QueryParams
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import MilestoneResponse
from app.services.project.milestone import MilestoneService

router = APIRouter()


@router.get("/", response_model=ResponseModel[PaginatedResponse[MilestoneResponse]])
def list_milestones(
    project_id: int = Path(..., description="项目ID"),
    params: QueryParams = Depends(QueryParams),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MilestoneService(db)
    result = service.list(
        params,
        extra_filters={"project_id": project_id},
    )
    return ResponseModel(
        data=PaginatedResponse(
            items=result.items,
            total=result.total,
            page=params.page,
            page_size=params.page_size,
            pages=result.pages,
        )
    )
```

### 1.3 创建/更新示例

```python
@router.post("/", response_model=ResponseModel[MilestoneResponse])
def create_milestone(
    project_id: int,
    payload: MilestoneCreate,
    db: Session = Depends(get_db),
):
    service = MilestoneService(db)
    data = payload.model_copy(update={"project_id": project_id})
    created = service.create(data)
    return ResponseModel(data=created)


@router.put("/{milestone_id}", response_model=ResponseModel[MilestoneResponse])
def update_milestone(
    milestone_id: int,
    payload: MilestoneUpdate,
    db: Session = Depends(get_db),
):
    service = MilestoneService(db)
    return ResponseModel(data=service.update(milestone_id, payload))
```

> 🔁 `service.list()` 返回 `PaginatedResult`，可直接 `.items/.total/.pages`。  
> 🔒 `unique_fields` 或 `service.create(..., check_unique=("milestone_code",))` 自动执行唯一性校验。  
> 🧱 钩子：`_before_create/_after_create/_before_list` 等用于插入业务逻辑。

---

## 二、兼容：SyncBaseService（旧版）

### 2.1 创建Service类

```python
from app.common.crud.sync_service import SyncBaseService
from app.models.project import ProjectMilestone
from app.schemas.project import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse
)
from sqlalchemy.orm import Session


class MilestoneService(
    SyncBaseService[ProjectMilestone, MilestoneCreate, MilestoneUpdate, MilestoneResponse]
):
    """里程碑服务"""
    
    def __init__(self, db: Session):
        super().__init__(
            model=ProjectMilestone,
            db=db,
            resource_name="里程碑"
        )
    
    def _to_response(self, obj: ProjectMilestone) -> MilestoneResponse:
        """将模型对象转换为响应对象"""
        return MilestoneResponse.model_validate(obj)
```

### 2.2 在API中使用

```python
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.services.projects.milestone_service import MilestoneService
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[MilestoneResponse])
def list_milestones(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """获取里程碑列表"""
    service = MilestoneService(db)
    
    # 构建筛选条件
    filters = {"project_id": project_id}
    if status:
        filters["status"] = status
    
    # 调用Service的list方法
    result = service.list(
        skip=(page - 1) * page_size,
        limit=page_size,
        filters=filters,
        keyword=keyword,
        keyword_fields=["milestone_name", "description"],
        order_by="planned_date",
        order_direction="desc"
    )
    
    return PaginatedResponse(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
        pages=(result["total"] + page_size - 1) // page_size
    )


@router.post("/", response_model=MilestoneResponse)
def create_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_in: MilestoneCreate = None,
    db: Session = Depends(get_db),
):
    """创建里程碑"""
    service = MilestoneService(db)
    
    # 确保使用项目ID
    milestone_data = milestone_in.model_dump()
    milestone_data["project_id"] = project_id
    milestone_create = MilestoneCreate(**milestone_data)
    
    return service.create(milestone_create)


@router.get("/{milestone_id}", response_model=MilestoneResponse)
def get_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(get_db),
):
    """获取里程碑详情"""
    service = MilestoneService(db)
    milestone = service.get(milestone_id)
    
    # 验证里程碑属于该项目
    if milestone.project_id != project_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="里程碑不存在"
        )
    
    return milestone


@router.put("/{milestone_id}", response_model=MilestoneResponse)
def update_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    milestone_in: MilestoneUpdate = None,
    db: Session = Depends(get_db),
):
    """更新里程碑"""
    service = MilestoneService(db)
    milestone = service.get(milestone_id)
    
    if milestone.project_id != project_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="里程碑不存在"
        )
    
    return service.update(milestone_id, milestone_in)


@router.delete("/{milestone_id}", status_code=204)
def delete_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(get_db),
):
    """删除里程碑"""
    service = MilestoneService(db)
    milestone = service.get(milestone_id)
    
    if milestone.project_id != project_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="里程碑不存在"
        )
    
    service.delete(milestone_id)
    return None
```

---

## 三、核心功能

### 3.1 Service基类提供的方法

| 方法 | 说明 | 示例 |
|------|------|------|
| `get(id)` | 获取单个对象 | `service.get(1)` |
| `list(...)` | 列表查询（支持筛选、搜索、排序、分页） | `service.list(filters={"status": "ACTIVE"})` |
| `create(obj_in)` | 创建对象 | `service.create(milestone_in)` |
| `update(id, obj_in)` | 更新对象 | `service.update(1, milestone_in)` |
| `delete(id)` | 删除对象 | `service.delete(1)` |
| `count(filters)` | 统计数量 | `service.count(filters={"status": "ACTIVE"})` |

### 3.2 筛选条件支持

```python
# 精确匹配
filters = {"status": "ACTIVE"}

# 列表匹配
filters = {"status": ["ACTIVE", "PENDING"]}

# 范围查询
filters = {"price": {"min": 100, "max": 1000}}

# 模糊匹配
filters = {"name": {"like": "test"}}

# 空值查询
filters = {"deleted_at": None}

# 组合查询
filters = {
    "status": "ACTIVE",
    "price": {"min": 100, "max": 1000},
    "name": {"like": "test"}
}
```

### 2.3 关键词搜索

```python
result = service.list(
    keyword="里程碑",
    keyword_fields=["milestone_name", "description"]
)
```

### 2.4 排序和分页

```python
result = service.list(
    skip=0,
    limit=100,
    order_by="planned_date",
    order_direction="desc"  # 或 "asc"
)
```

---

## 三、高级用法

### 3.1 唯一性检查

```python
# 创建时检查唯一性
service.create(
    milestone_in,
    check_unique={"code": milestone_in.code}
)

# 更新时检查唯一性（排除当前对象）
service.update(
    milestone_id,
    milestone_in,
    check_unique={"code": milestone_in.code}
)
```

### 3.2 关系预加载

```python
# 获取对象时预加载关系
milestone = service.get(
    milestone_id,
    load_relationships=["project", "tasks"]
)

# 列表查询时预加载关系
result = service.list(
    load_relationships=["project"]
)
```

### 3.3 钩子方法

```python
class MilestoneService(SyncBaseService[...]):
    
    def _before_create(self, obj_in: MilestoneCreate) -> MilestoneCreate:
        """创建前钩子：自动设置默认值"""
        # 例如：自动生成编码
        if not obj_in.code:
            obj_in.code = self._generate_code()
        return obj_in
    
    def _after_create(self, db_obj: ProjectMilestone) -> ProjectMilestone:
        """创建后钩子：发送通知等"""
        # 例如：发送通知
        self._send_notification(db_obj)
        return db_obj
    
    def _before_update(self, id: int, obj_in: MilestoneUpdate, db_obj: ProjectMilestone) -> MilestoneUpdate:
        """更新前钩子"""
        return obj_in
    
    def _after_update(self, db_obj: ProjectMilestone) -> ProjectMilestone:
        """更新后钩子"""
        return db_obj
    
    def _before_delete(self, id: int) -> None:
        """删除前钩子"""
        pass
    
    def _after_delete(self, id: int) -> None:
        """删除后钩子"""
        pass
```

### 3.4 自定义方法

```python
class MilestoneService(SyncBaseService[...]):
    
    def list_by_project(
        self,
        project_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取项目的里程碑列表（自定义方法）"""
        filters = {"project_id": project_id}
        if status:
            filters["status"] = status
        
        return self.list(
            skip=skip,
            limit=limit,
            filters=filters,
            order_by="planned_date",
            order_direction="desc"
        )
    
    def create_for_project(
        self,
        project_id: int,
        milestone_in: MilestoneCreate
    ) -> MilestoneResponse:
        """为项目创建里程碑（自定义方法）"""
        milestone_data = milestone_in.model_dump()
        milestone_data["project_id"] = project_id
        milestone_create = MilestoneCreate(**milestone_data)
        return self.create(milestone_create)
```

---

## 四、与异步版本的区别

| 特性 | 同步版本 | 异步版本 |
|------|---------|---------|
| Session类型 | `Session` | `AsyncSession` |
| 方法定义 | 普通方法 | `async def` |
| 方法调用 | 直接调用 | `await` |
| 关系加载 | `joinedload` | `selectinload` |
| 查询方式 | `db.query()` | `select()` + `await db.execute()` |

---

## 五、迁移建议

### 5.1 何时使用同步版本

- ✅ 当前项目使用同步Session
- ✅ 不需要高并发性能
- ✅ 快速减少重复代码

### 5.2 何时考虑异步版本

- ⚠️ 需要高并发性能
- ⚠️ 未来计划迁移到异步
- ⚠️ 有大量I/O操作

### 5.3 迁移路径

1. **第一阶段**: 使用同步版本重构现有代码
2. **第二阶段**: 逐步迁移到异步版本（如果需要）

---

## 六、完整示例

查看 `app/common/crud/sync_example_usage.py` 获取完整示例代码。

---

## 七、常见问题

### Q1: 为什么需要实现 `_to_response` 方法？

**A**: 因为 `ResponseSchemaType` 是泛型类型变量，不能直接实例化。子类需要实现具体的转换逻辑。

### Q2: 如何处理复杂的业务逻辑？

**A**: 可以在Service类中添加自定义方法，或使用钩子方法（`_before_create`、`_after_create`等）。

### Q3: 如何添加权限检查？

**A**: 在API层添加权限检查，Service层专注于业务逻辑。

### Q4: 如何处理事务？

**A**: Service层会自动提交事务（`commit=True`）。如果需要手动控制，可以在Repository层设置 `commit=False`。

---

**文档版本**: v1.0  
**最后更新**: 2026-01-24
