# 通用CRUD基类快速开始指南

## 5分钟快速上手

### 步骤1: 创建Service类（只需3行代码！）

```python
from app.common.crud.service import BaseService
from app.models.projects import Project
from app.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse

class ProjectService(
    BaseService[Project, ProjectCreate, ProjectUpdate, ProjectResponse]
):
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db, "项目")
```

### 步骤2: 在API中使用

```python
@router.get("/", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    page: int = Query(1),
    page_size: int = Query(20),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    service = ProjectService(db)
    
    # 构建筛选条件
    filters = {}
    if status:
        filters["status"] = status
    
    # 一行代码完成所有查询逻辑！
    result = await service.list(
        skip=(page - 1) * page_size,
        limit=page_size,
        filters=filters,
        keyword=keyword,
        keyword_fields=["code", "name"],
        order_by="created_at",
        order_direction="desc"
    )
    
    return PaginatedResponse(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size
    )
```

### 步骤3: 完成！

就这么简单！你现在已经拥有了：
- ✅ 完整的CRUD操作
- ✅ 筛选、搜索、排序、分页
- ✅ 自动唯一性检查
- ✅ 统一的错误处理

---

## 支持的筛选方式

```python
filters = {
    # 精确匹配
    "status": "ACTIVE",
    
    # 列表匹配
    "type": ["TYPE_A", "TYPE_B"],
    
    # 范围查询
    "price": {"min": 100, "max": 1000},
    "progress": {"min": 50, "max": 100},
    
    # 模糊匹配
    "name": {"like": "test"},
    
    # NULL查询
    "deleted_at": {"is_null": True},
    
    # IN查询
    "id": {"in": [1, 2, 3]},
    
    # NOT IN查询
    "category_id": {"not_in": [5, 6]}
}
```

---

## 完整API示例

```python
@router.get("/{id}", response_model=ProjectResponse)
async def get_project(id: int, db: AsyncSession = Depends(get_db)):
    service = ProjectService(db)
    return await service.get(id)

@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    service = ProjectService(db)
    return await service.create(project_in)

@router.put("/{id}", response_model=ProjectResponse)
async def update_project(
    id: int,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    service = ProjectService(db)
    return await service.update(id, project_in)

@router.delete("/{id}", status_code=204)
async def delete_project(
    id: int,
    soft_delete: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    service = ProjectService(db)
    await service.delete(id, soft_delete=soft_delete)
    return None
```

---

## 扩展功能

### 添加业务特定方法

```python
class ProjectService(BaseService[...]):
    async def get_by_code(self, code: str):
        """根据编码获取项目"""
        return await self.get_by_field("code", code)
    
    async def start_project(self, project_id: int):
        """启动项目（业务逻辑）"""
        project = await self.get(project_id)
        # 业务逻辑...
        return project
```

### 使用钩子方法

```python
class ProjectService(BaseService[...]):
    async def _before_create(self, obj_in: ProjectCreate):
        """创建前自动生成编码"""
        if not obj_in.code:
            obj_in.code = await self._generate_code()
        return obj_in
    
    async def _after_create(self, db_obj: Project):
        """创建后发送通知"""
        await send_notification(db_obj)
        return db_obj
```

---

## 更多示例

查看 `example_usage.py` 获取更多使用示例。
