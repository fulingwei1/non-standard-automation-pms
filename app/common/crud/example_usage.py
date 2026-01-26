# -*- coding: utf-8 -*-
"""
通用CRUD基类使用示例
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel

from app.common.crud.service import BaseService
from app.models.projects import Project
from app.schemas.projects import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse
)
from app.schemas.common import PaginatedResponse
from app.api.dependencies import get_db, get_current_user

router = APIRouter()


# ========== 示例1: 最简单的Service实现 ==========

class ProjectService(
    BaseService[Project, ProjectCreate, ProjectUpdate, ProjectResponse]
):
    """项目服务（只需3行代码！）"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(
            model=Project,
            db=db,
            resource_name="项目"
        )


# ========== 示例2: 带业务逻辑的Service实现 ==========

class ProjectServiceAdvanced(
    BaseService[Project, ProjectCreate, ProjectUpdate, ProjectResponse]
):
    """项目服务（带业务逻辑）"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db, "项目")
    
    async def get_by_code(self, code: str) -> Optional[ProjectResponse]:
        """根据项目编码获取项目"""
        return await self.get_by_field("code", code)
    
    async def create(
        self,
        obj_in: ProjectCreate,
        *,
        check_unique: Optional[Dict[str, Any]] = None
    ) -> ProjectResponse:
        """创建项目（自动检查编码唯一性）"""
        # 自动添加编码唯一性检查
        if check_unique is None:
            check_unique = {}
        check_unique["code"] = obj_in.code
        
        return await super().create(obj_in, check_unique=check_unique)
    
    async def _before_create(self, obj_in: ProjectCreate) -> ProjectCreate:
        """创建前处理：自动生成项目编码"""
        if not obj_in.code:
            # 生成项目编码逻辑
            obj_in.code = await self._generate_project_code()
        return obj_in
    
    async def _generate_project_code(self) -> str:
        """生成项目编码"""
        from datetime import datetime
        date_str = datetime.now().strftime("%y%m%d")
        # 查询当天已有项目数
        count = await self.count(filters={"code": {"like": f"PJ{date_str}"}})
        return f"PJ{date_str}{count + 1:03d}"


# ========== 示例3: API路由使用 ==========

@router.get("/", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    min_progress: Optional[float] = Query(None, description="最小进度"),
    max_progress: Optional[float] = Query(None, description="最大进度"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取项目列表（自动支持筛选、搜索、排序、分页）"""
    service = ProjectService(db)
    
    # 构建筛选条件
    filters = {}
    if status:
        filters["status"] = status
    if customer_id:
        filters["customer_id"] = customer_id
    if min_progress is not None or max_progress is not None:
        filters["progress"] = {}
        if min_progress is not None:
            filters["progress"]["min"] = min_progress
        if max_progress is not None:
            filters["progress"]["max"] = max_progress
    
    # 关键词搜索字段
    keyword_fields = ["code", "name", "contract_no"]
    
    # 调用服务（一行代码完成所有查询逻辑！）
    result = await service.list(
        skip=(page - 1) * page_size,
        limit=page_size,
        filters=filters,
        keyword=keyword,
        keyword_fields=keyword_fields,
        order_by="created_at",
        order_direction="desc"
    )
    
    return PaginatedResponse(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
        pages=(result["total"] + page_size - 1) // page_size
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int = Path(..., description="项目ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取项目详情"""
    service = ProjectService(db)
    return await service.get(project_id)


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建项目"""
    service = ProjectService(db)
    return await service.create(project_in)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int = Path(..., description="项目ID"),
    project_in: ProjectUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新项目"""
    service = ProjectService(db)
    return await service.update(project_id, project_in)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int = Path(..., description="项目ID"),
    soft_delete: bool = Query(False, description="是否软删除"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除项目"""
    service = ProjectService(db)
    await service.delete(project_id, soft_delete=soft_delete)
    return None


# ========== 示例4: 复杂筛选查询 ==========

@router.get("/advanced-search", response_model=PaginatedResponse[ProjectResponse])
async def advanced_search(
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db)
):
    """高级搜索示例"""
    service = ProjectService(db)
    
    # 复杂筛选条件
    filters = {
        # 精确匹配
        "status": "ACTIVE",
        
        # 列表匹配
        "type": ["TYPE_A", "TYPE_B"],
        
        # 范围查询
        "progress": {"min": 50, "max": 100},
        
        # 模糊匹配
        "name": {"like": "测试"},
        
        # NULL查询
        "deleted_at": {"is_null": True},
        
        # IN查询
        "customer_id": {"in": [1, 2, 3]},
    }
    
    result = await service.list(
        skip=(page - 1) * page_size,
        limit=page_size,
        filters=filters,
        keyword="项目",
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
