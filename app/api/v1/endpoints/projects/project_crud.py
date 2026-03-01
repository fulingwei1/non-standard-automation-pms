# -*- coding: utf-8 -*-
"""
项目模块 - 基础CRUD操作（薄Controller层）

包含项目列表、创建、详情、更新、删除
业务逻辑已提取到 app.services.project_crud.ProjectCrudService
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_crud import ProjectCrudService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=PaginatedResponse[ProjectListResponse])


@router.get("/my-projects", response_model=PaginatedResponse[ProjectListResponse])
def read_my_projects(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    is_active: Optional[bool] = Query(True, description="是否启用"),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """
    获取我参与的项目列表（基于项目成员关系）
    """
    from app.models.project import Project
    from app.models.project.team import ProjectMember
    
    # 查询用户参与的项目 ID
    member_project_ids = (
        db.query(ProjectMember.project_id)
        .filter(ProjectMember.user_id == current_user.id, ProjectMember.is_active == True)
        .all()
    )
    project_ids = [pid[0] for pid in member_project_ids]
    
    # 如果没有参与任何项目，返回空列表
    if not project_ids:
        return PaginatedResponse(items=[], total=0, page=pagination.page, page_size=pagination.page_size, pages=0)
    
    service = ProjectCrudService(db)
    items, total = service.list_projects(
        offset=pagination.offset,
        limit=pagination.limit,
        keyword=keyword,
        is_active=is_active,
        project_ids=project_ids,  # 只返回参与的项目
    )
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )

def read_projects(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（项目名称/编码/合同编号）"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    stage: Optional[str] = Query(None, description="阶段筛选（S1-S9）"),
    status: Optional[str] = Query(None, description="状态筛选（ST01-ST30）"),
    health: Optional[str] = Query(None, description="健康度筛选（H1-H4）"),
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    pm_id: Optional[int] = Query(None, description="项目经理ID筛选"),
    min_progress: Optional[float] = Query(None, ge=0, le=100, description="最小进度百分比"),
    max_progress: Optional[float] = Query(None, ge=0, le=100, description="最大进度百分比"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    include_cost: bool = Query(False, description="是否包含成本摘要"),
    overrun_only: bool = Query(False, description="仅显示超支项目"),
    sort: Optional[str] = Query(
        None, 
        description="排序方式：cost_desc/cost_asc/budget_used_pct/created_at_desc（默认）"
    ),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目列表（支持分页、搜索、筛选、成本展示）
    """
    service = ProjectCrudService(db)

    # 判断是否使用缓存
    use_cache = (
        not keyword 
        and not any([customer_id, stage, status, health, project_type, pm_id, min_progress, max_progress])
        and not include_cost
        and not overrun_only
        and not sort
    )

    # 尝试从缓存读取
    if use_cache:
        try:
            from app.services.cache_service import CacheService
            cache_service = CacheService()
            cache_key_params = {
                "page": pagination.page,
                "page_size": pagination.page_size,
                "is_active": is_active,
            }
            cached_data = cache_service.get_project_list(**cache_key_params)
            if cached_data:
                return PaginatedResponse(**cached_data)
        except Exception:
            logger.debug("项目列表缓存读取失败，继续查询数据库", exc_info=True)

    # 从服务层获取项目列表
    projects, total = service.get_projects_with_pagination(
        pagination=pagination,
        keyword=keyword,
        customer_id=customer_id,
        stage=stage,
        status=status,
        health=health,
        project_type=project_type,
        pm_id=pm_id,
        min_progress=min_progress,
        max_progress=max_progress,
        is_active=is_active,
        overrun_only=overrun_only,
        sort=sort,
        current_user=current_user,
    )

    # 补充冗余字段
    service.populate_redundant_fields(projects)

    # 批量获取成本数据（如果需要）
    cost_summaries = {}
    if include_cost and projects:
        from app.services.project_cost_aggregation_service import ProjectCostAggregationService
        cost_service = ProjectCostAggregationService(db)
        project_ids = [p.id for p in projects]
        cost_summaries = cost_service.get_projects_cost_summary(
            project_ids, include_breakdown=True
        )

    # 计算分页
    pages = pagination.pages_for_total(total)

    # 转换为响应对象
    project_items = []
    for p in projects:
        item_dict = {
            "id": p.id,
            "project_code": p.project_code,
            "project_name": p.project_name,
            "customer_name": p.customer_name,
            "stage": p.stage,
            "health": p.health,
            "progress_pct": p.progress_pct,
            "pm_name": p.pm_name,
            "pm_id": p.pm_id,
            "sales_id": p.salesperson_id,
            "te_id": getattr(p, "te_id", None),
            "cost_summary": cost_summaries.get(p.id) if include_cost else None,
        }
        project_items.append(ProjectListResponse(**item_dict))

    result = PaginatedResponse(
        items=project_items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages
    )

    # 存入缓存（仅在不包含成本数据时）
    if use_cache:
        try:
            from app.core.config import settings
            from app.services.cache_service import CacheService
            cache_service = CacheService()
            cache_service.set_project_list(
                result.model_dump(),
                expire_seconds=settings.REDIS_CACHE_PROJECT_LIST_TTL,
                **cache_key_params
            )
        except Exception:
            logger.debug("项目列表缓存写入失败，忽略", exc_info=True)

    return result


@router.post("/", response_model=ProjectResponse)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: ProjectCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Create new project.
    """
    service = ProjectCrudService(db)
    project = service.create_project(project_in)
    return project


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def read_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Path(..., description="项目ID"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Get project by ID.
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id, "您没有权限查看该项目")

    service = ProjectCrudService(db)
    
    # 获取项目基础信息
    project = service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取项目成员
    members = service.get_project_members(project_id)

    # 获取设备和里程碑
    machines = service.get_project_machines(project)
    milestones = service.get_project_milestones(project)

    # 构建响应
    project_base = ProjectResponse.model_validate(project)
    project_detail = ProjectDetailResponse(
        **project_base.model_dump(),
        members=members,
        machines=machines,
        milestones=milestones
    )

    # 存入缓存
    if use_cache:
        try:
            from app.core.config import settings
            from app.services.cache_service import CacheService
            cache_service = CacheService()
            project_dict = {
                "id": project.id,
                "project_code": project.project_code,
                "project_name": project.project_name,
            }
            cache_service.set_project_detail(
                project_id,
                project_dict,
                expire_seconds=settings.REDIS_CACHE_PROJECT_DETAIL_TTL
            )
        except Exception:
            logger.debug("项目详情缓存写入失败，忽略", exc_info=True)

    return project_detail


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Update a project.
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id, "您没有权限修改该项目")

    service = ProjectCrudService(db)
    update_data = project_in.model_dump(exclude_unset=True)
    updated_project = service.update_project(project, update_data)

    # 使缓存失效
    service.invalidate_project_cache(project_id)

    return updated_project


@router.delete("/{project_id}", response_model=ResponseModel)
def delete_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Delete a project (soft delete).
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id, "您没有权限删除该项目")

    service = ProjectCrudService(db)
    service.soft_delete_project(project)

    # 使缓存失效
    service.invalidate_project_cache(project_id)

    return ResponseModel(
        code=200,
        message="项目删除成功",
        data={"id": project_id}
    )
