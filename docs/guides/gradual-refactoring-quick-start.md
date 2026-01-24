# 渐进式重构快速启动指南

> **目标**: 在2小时内完成第一个模块的迁移，验证方案可行性

---

## 第一步：创建同步CRUD基类（1小时）

### 1.1 创建同步Repository基类

**文件**: `app/common/crud/sync_repository.py`

```python
# -*- coding: utf-8 -*-
"""
同步版本的Repository基类
适配当前项目使用的同步Session
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class SyncBaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """同步版本的Repository基类"""
    
    def __init__(
        self,
        model: Type[ModelType],
        db: Session,
        resource_name: str = None
    ):
        self.model = model
        self.db = db
        self.resource_name = resource_name or model.__name__
    
    def get(self, id: int) -> Optional[ModelType]:
        """根据ID获取单个对象"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        keyword: Optional[str] = None,
        keyword_fields: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "desc"
    ) -> tuple[List[ModelType], int]:
        """列表查询"""
        query = self.db.query(self.model)
        
        # 应用筛选条件
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        # 关键词搜索
        if keyword and keyword_fields:
            conditions = []
            for field in keyword_fields:
                if hasattr(self.model, field):
                    conditions.append(getattr(self.model, field).contains(keyword))
            if conditions:
                query = query.filter(or_(*conditions))
        
        # 排序
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            if order_direction.lower() == "asc":
                query = query.order_by(order_field.asc())
            else:
                query = query.order_by(order_field.desc())
        
        # 总数
        total = query.count()
        
        # 分页
        items = query.offset(skip).limit(limit).all()
        
        return list(items), total
    
    def create(
        self,
        obj_in: CreateSchemaType,
        *,
        commit: bool = True
    ) -> ModelType:
        """创建对象"""
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        if commit:
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    def update(
        self,
        id: int,
        obj_in: UpdateSchemaType,
        *,
        commit: bool = True
    ) -> Optional[ModelType]:
        """更新对象"""
        db_obj = self.get(id)
        if not db_obj:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        if commit:
            self.db.commit()
            self.db.refresh(db_obj)
        
        return db_obj
    
    def delete(
        self,
        id: int,
        *,
        commit: bool = True
    ) -> bool:
        """删除对象"""
        db_obj = self.get(id)
        if not db_obj:
            return False
        
        self.db.delete(db_obj)
        if commit:
            self.db.commit()
        
        return True
```

### 1.2 创建同步Service基类

**文件**: `app/common/crud/sync_service.py`

```python
# -*- coding: utf-8 -*-
"""
同步版本的Service基类
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi import HTTPException, status

from app.common.crud.sync_repository import SyncBaseRepository

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class SyncBaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    """同步版本的Service基类"""
    
    def __init__(
        self,
        model: Type[ModelType],
        db: Session,
        resource_name: str = None
    ):
        self.model = model
        self.db = db
        self.resource_name = resource_name or model.__name__
        self.repository = SyncBaseRepository(model, db, resource_name)
    
    def get(self, id: int) -> ResponseSchemaType:
        """获取单个对象"""
        obj = self.repository.get(id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.resource_name} not found"
            )
        return ResponseSchemaType.model_validate(obj)
    
    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        keyword: Optional[str] = None,
        keyword_fields: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "desc"
    ) -> Dict[str, Any]:
        """列表查询"""
        items, total = self.repository.list(
            skip=skip,
            limit=limit,
            filters=filters,
            keyword=keyword,
            keyword_fields=keyword_fields,
            order_by=order_by,
            order_direction=order_direction
        )
        
        return {
            "items": [ResponseSchemaType.model_validate(item) for item in items],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    def create(self, obj_in: CreateSchemaType) -> ResponseSchemaType:
        """创建对象"""
        db_obj = self.repository.create(obj_in)
        return ResponseSchemaType.model_validate(db_obj)
    
    def update(self, id: int, obj_in: UpdateSchemaType) -> ResponseSchemaType:
        """更新对象"""
        db_obj = self.repository.update(id, obj_in)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.resource_name} not found"
            )
        return ResponseSchemaType.model_validate(db_obj)
    
    def delete(self, id: int) -> bool:
        """删除对象"""
        success = self.repository.delete(id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.resource_name} not found"
            )
        return success
```

### 1.3 更新__init__.py

**文件**: `app/common/crud/__init__.py`

```python
# 添加同步版本导出
from app.common.crud.sync_repository import SyncBaseRepository
from app.common.crud.sync_service import SyncBaseService

__all__ = [
    # ... 现有导出
    "SyncBaseRepository",
    "SyncBaseService",
]
```

---

## 第二步：试点迁移里程碑模块（1小时）

### 2.1 创建MilestoneService

**文件**: `app/services/projects/milestone_service.py`

```python
# -*- coding: utf-8 -*-
"""
项目里程碑服务
"""

from sqlalchemy.orm import Session

from app.common.crud.sync_service import SyncBaseService
from app.models.project import ProjectMilestone
from app.schemas.project import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse
)


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
    
    def list_by_project(
        self,
        project_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取项目的里程碑列表"""
        filters = {"project_id": project_id}
        if status:
            filters["status"] = status
        
        return self.list(
            skip=skip,
            limit=limit,
            filters=filters,
            keyword=keyword,
            keyword_fields=["milestone_name", "description"],
            order_by="planned_date",
            order_direction="desc"
        )
    
    def create_for_project(
        self,
        project_id: int,
        milestone_in: MilestoneCreate
    ) -> MilestoneResponse:
        """为项目创建里程碑"""
        # 确保使用项目ID
        milestone_data = milestone_in.model_dump()
        milestone_data["project_id"] = project_id
        
        from app.schemas.project import MilestoneCreate
        milestone_create = MilestoneCreate(**milestone_data)
        
        return self.create(milestone_create)
```

### 2.2 重构API端点

**文件**: `app/api/v1/endpoints/projects/milestones/crud.py`

```python
# -*- coding: utf-8 -*-
"""
项目里程碑 CRUD 操作（重构版本）
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.project import MilestoneCreate, MilestoneResponse, MilestoneUpdate
from app.schemas.common import PaginatedResponse
from app.utils.permission_helpers import check_project_access_or_raise
from app.services.projects.milestone_service import MilestoneService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[MilestoneResponse])
def read_project_milestones(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None, description="里程碑状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """获取项目的里程碑列表"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = MilestoneService(db)
    result = service.list_by_project(
        project_id=project_id,
        skip=(page - 1) * page_size,
        limit=page_size,
        status=status,
        keyword=keyword
    )
    
    return PaginatedResponse(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
        pages=(result["total"] + page_size - 1) // page_size
    )


@router.post("/", response_model=MilestoneResponse)
def create_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_in: MilestoneCreate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:create")),
) -> Any:
    """为项目创建里程碑"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = MilestoneService(db)
    return service.create_for_project(project_id, milestone_in)


@router.get("/{milestone_id}", response_model=MilestoneResponse)
def read_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """获取项目里程碑详情"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = MilestoneService(db)
    milestone = service.get(milestone_id)
    
    # 验证里程碑属于该项目
    if milestone.project_id != project_id:
        raise HTTPException(status_code=404, detail="里程碑不存在")
    
    return milestone


@router.put("/{milestone_id}", response_model=MilestoneResponse)
def update_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    milestone_in: MilestoneUpdate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:update")),
) -> Any:
    """更新项目里程碑"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = MilestoneService(db)
    milestone = service.get(milestone_id)
    
    # 验证里程碑属于该项目
    if milestone.project_id != project_id:
        raise HTTPException(status_code=404, detail="里程碑不存在")
    
    return service.update(milestone_id, milestone_in)


@router.delete("/{milestone_id}", status_code=204)
def delete_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:delete")),
) -> Any:
    """删除项目里程碑"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = MilestoneService(db)
    milestone = service.get(milestone_id)
    
    # 验证里程碑属于该项目
    if milestone.project_id != project_id:
        raise HTTPException(status_code=404, detail="里程碑不存在")
    
    service.delete(milestone_id)
    return None
```

### 2.3 运行测试

```bash
# 运行API测试
pytest tests/api/v1/test_milestones.py -v

# 运行集成测试
pytest tests/integration/test_milestones.py -v
```

---

## 第三步：验证和对比（30分钟）

### 3.1 代码行数对比

```bash
# 统计重构前代码行数
wc -l app/api/v1/endpoints/projects/milestones/crud.py

# 统计重构后代码行数
wc -l app/api/v1/endpoints/projects/milestones/crud.py
wc -l app/services/projects/milestone_service.py
wc -l app/common/crud/sync_*.py

# 计算减少比例
```

### 3.2 功能验证

- [ ] 列表查询正常
- [ ] 创建功能正常
- [ ] 更新功能正常
- [ ] 删除功能正常
- [ ] 权限检查正常
- [ ] 关键词搜索正常

### 3.3 性能验证

```bash
# 运行性能测试
pytest tests/performance/test_milestones.py -v
```

---

## 预期结果

### 代码量减少

| 文件 | 重构前 | 重构后 | 减少 |
|------|--------|--------|------|
| `crud.py` | ~150行 | ~80行 | 47% |
| 新增 `service.py` | - | ~50行 | - |
| **总计** | **~150行** | **~130行** | **13%** |

**注意**: 虽然单文件减少不多，但Service可以复用，后续模块迁移时收益更大。

### 代码质量提升

- ✅ 业务逻辑与API层分离
- ✅ 代码更易测试
- ✅ 代码更易维护
- ✅ 统一的代码模式

---

## 下一步

如果试点迁移成功：

1. **继续迁移其他模块** (Week 3-4)
   - 成本模块
   - 机器模块
   - 成员模块

2. **完善基础设施** (Week 1-2)
   - 添加更多功能
   - 优化性能
   - 完善文档

3. **推广到其他模块** (Week 5+)
   - 服务层重构
   - 前端组件重构

---

## 常见问题

### Q1: 为什么需要同步版本？

**A**: 当前项目使用同步Session，而现有CRUD基类使用AsyncSession。创建同步版本可以：
- 立即使用，无需迁移到异步
- 降低风险，保持现有架构
- 未来可以逐步迁移到异步

### Q2: Service层是否必要？

**A**: 是的，Service层的好处：
- 业务逻辑与API层分离
- 代码更易测试
- 可以在多个API端点复用
- 符合分层架构原则

### Q3: 如何保留自定义端点？

**A**: 可以在Service中添加自定义方法，或在API层直接实现：

```python
# 方式1: 在Service中添加
class MilestoneService(SyncBaseService):
    def complete(self, milestone_id: int) -> MilestoneResponse:
        # 自定义逻辑
        pass

# 方式2: 在API层实现
@router.put("/{milestone_id}/complete")
def complete_milestone(...):
    # 直接实现
    pass
```

---

**开始时间**: ________  
**完成时间**: ________  
**遇到的问题**: ________
