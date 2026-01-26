# -*- coding: utf-8 -*-
"""
项目模块 - 基础CRUD操作

包含项目列表、创建、详情、更新、删除
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Customer, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=PaginatedResponse[ProjectListResponse])
def read_projects(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
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
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目列表（支持分页、搜索、筛选）
    """
    query = db.query(Project)

    # 关键词搜索
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Project.project_name.like(keyword_pattern),
                Project.project_code.like(keyword_pattern),
                Project.contract_no.like(keyword_pattern),
            )
        )

    # 客户筛选
    if customer_id:
        query = query.filter(Project.customer_id == customer_id)

    # 阶段筛选
    if stage:
        query = query.filter(Project.stage == stage)

    # 状态筛选
    if status:
        query = query.filter(Project.status == status)

    # 健康度筛选
    if health:
        query = query.filter(Project.health == health)

    # 项目类型筛选
    if project_type:
        query = query.filter(Project.project_type == project_type)

    # 项目经理筛选
    if pm_id:
        query = query.filter(Project.pm_id == pm_id)

    # 进度筛选
    if min_progress is not None:
        query = query.filter(Project.progress_pct >= min_progress)
    if max_progress is not None:
        query = query.filter(Project.progress_pct <= max_progress)

    # 是否启用筛选
    if is_active is not None:
        query = query.filter(Project.is_active == is_active)

    # 应用数据权限过滤
    from app.services.data_scope import DataScopeService
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    # 使用selectinload优化关联查询
    query = query.options(
        selectinload(Project.customer),
        selectinload(Project.manager)
    )

    # 缓存逻辑
    use_cache = not keyword and not any([customer_id, stage, status, health, project_type, pm_id, min_progress, max_progress])
    if use_cache:
        try:
            from app.services.cache_service import CacheService
            cache_service = CacheService()
            cache_key_params = {
                "page": page,
                "page_size": page_size,
                "is_active": is_active,
            }
            cached_data = cache_service.get_project_list(**cache_key_params)
            if cached_data:
                return PaginatedResponse(**cached_data)
        except Exception:
            logger.debug("项目列表缓存读取失败，继续查询数据库", exc_info=True)

    # 总数统计
    try:
        count_result = query.count()
        total = int(count_result) if count_result is not None else 0
    except Exception:
        logger.debug("项目列表统计总数失败，降级为 0", exc_info=True)
        total = 0

    # 分页
    offset = (page - 1) * page_size
    projects = query.order_by(desc(Project.created_at)).offset(offset).limit(page_size).all()

    # 补充冗余字段
    for project in projects:
        if not project.customer_name and project.customer:
            project.customer_name = project.customer.customer_name
        if not project.pm_name and project.manager:
            project.pm_name = project.manager.real_name or project.manager.username

    total = int(total) if total is not None else 0
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    # 转换为响应对象，映射字段
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
            "sales_id": p.salesperson_id,  # 映射 salesperson_id -> sales_id
            "te_id": getattr(p, "te_id", None),  # 技术负责人ID（如有）
        }
        project_items.append(ProjectListResponse(**item_dict))

    result = PaginatedResponse(
        items=project_items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )

    # 存入缓存
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
    project = (
        db.query(Project)
        .filter(Project.project_code == project_in.project_code)
        .first()
    )
    if project:
        raise HTTPException(
            status_code=400,
            detail="The project with this project number already exists in the system.",
        )

    project_data = project_in.model_dump()
    project_data.pop("machine_count", None)

    project = Project(**project_data)

    # Populate redundant fields
    if project.customer_id:
        customer = db.query(Customer).get(project.customer_id)
        if customer:
            project.customer_name = customer.customer_name
            project.customer_contact = customer.contact_person
            project.customer_phone = customer.contact_phone

    if project.pm_id:
        pm = db.query(User).get(project.pm_id)
        if pm:
            project.pm_name = pm.real_name or pm.username

    db.add(project)
    db.commit()
    db.refresh(project)

    # Initialize standard stages
    from app.utils.project_utils import init_project_stages
    init_project_stages(db, project.id)

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

    project = (
        db.query(Project)
        .options(
            joinedload(Project.customer),
            joinedload(Project.manager),
        )
        .filter(Project.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 补充冗余字段
    if not project.customer_name and project.customer:
        project.customer_name = project.customer.customer_name
        project.customer_contact = project.customer.contact_person
        project.customer_phone = project.customer.contact_phone
    if not project.pm_name and project.manager:
        project.pm_name = project.manager.real_name or project.manager.username

    # 加载项目成员
    from app.models.project import ProjectMember
    from app.schemas.project import ProjectMemberResponse
    members_query = (
        db.query(ProjectMember)
        .options(joinedload(ProjectMember.user))
        .filter(ProjectMember.project_id == project_id)
        .all()
    )

    members = []
    for member in members_query:
        member_data = {
            "id": member.id,
            "project_id": member.project_id,
            "user_id": member.user_id,
            "username": member.user.username if member.user else f"user_{member.user_id}",
            "real_name": member.user.real_name if member.user and member.user.real_name else None,
            "role_code": member.role_code,
            "allocation_pct": member.allocation_pct,
            "start_date": member.start_date,
            "end_date": member.end_date,
            "is_active": member.is_active,
            "remark": member.remark,
        }
        members.append(ProjectMemberResponse(**member_data))

    # 加载machines和milestones
    from app.schemas.project import MachineResponse, MilestoneResponse
    machines_query = project.machines.all() if hasattr(project.machines, 'all') else []
    machines = [MachineResponse.model_validate(m) for m in machines_query]

    milestones_query = project.milestones.all() if hasattr(project.milestones, 'all') else []
    milestones = [MilestoneResponse.model_validate(m) for m in milestones_query]

    # 构建响应
    from app.schemas.project import ProjectDetailResponse, ProjectResponse
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

    update_data = project_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(project, field):
            setattr(project, field, value)

    # Update redundant fields if ID changed
    if "customer_id" in update_data:
        customer = db.query(Customer).get(project.customer_id)
        if customer:
            project.customer_name = customer.customer_name
            project.customer_contact = customer.contact_person
            project.customer_phone = customer.contact_phone

    if "pm_id" in update_data:
        pm = db.query(User).get(project.pm_id)
        if pm:
            project.pm_name = pm.real_name or pm.username

    db.add(project)
    db.commit()

    # 使项目缓存失效
    try:
        from app.services.cache_service import CacheService
        cache_service = CacheService()
        cache_service.invalidate_project_detail(project_id)
        cache_service.invalidate_project_list()
    except Exception:
        logger.debug("项目缓存失效失败，忽略", exc_info=True)

    db.refresh(project)
    return project


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

    project.is_active = False
    db.add(project)
    db.commit()

    # 使缓存失效
    try:
        from app.services.cache_service import CacheService
        cache_service = CacheService()
        cache_service.invalidate_project_detail(project_id)
        cache_service.invalidate_project_list()
    except Exception:
        logger.debug("项目缓存失效失败，忽略", exc_info=True)

    return ResponseModel(
        code=200,
        message="项目删除成功",
        data={"id": project_id}
    )
