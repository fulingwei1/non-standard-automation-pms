# 通用CRUD基类使用指南

## 快速开始

### 1. 创建Service类

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

### 2. 在API中使用

```python
@router.get("/", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    page: int = Query(1),
    page_size: int = Query(20),
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    service = ProjectService(db)
    result = await service.list(
        skip=(page - 1) * page_size,
        limit=page_size,
        keyword=keyword,
        keyword_fields=["code", "name"]
    )
    return PaginatedResponse(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size
    )
```

## 完整文档

详细实现代码请查看：`docs/design/通用CRUD基类完整实现.md`
