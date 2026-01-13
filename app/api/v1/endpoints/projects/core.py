# -*- coding: utf-8 -*-
"""
项目模块基础CRUD端点

包含项目列表、创建、详情、更新、删除、看板、统计、克隆等基础操作
"""

from typing import Any, List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path, status
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import (
    Project, Customer, ProjectStatusLog, ProjectPaymentPlan,
    ProjectMilestone, Machine, ProjectStage, ProjectMember
)
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectDetailResponse,
    ProjectCloneRequest,
    ProjectSummaryResponse,
    ProjectDashboardResponse,
    InProductionProjectSummary,
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


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

    # 启用状态筛选
    if is_active is not None:
        query = query.filter(Project.is_active == is_active)

    # 应用数据权限过滤
    from app.services.data_scope_service import DataScopeService
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    # 总数统计
    try:
        count_result = query.count()
        total = int(count_result) if count_result is not None else 0
    except Exception:
        total = 0

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
            pass

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

    project_items = [ProjectListResponse.model_validate(p) for p in projects]

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
            from app.services.cache_service import CacheService
            cache_service = CacheService()
            cache_service.set_project_list(
                result.model_dump(),
                expire_seconds=settings.REDIS_CACHE_PROJECT_LIST_TTL,
                **cache_key_params
            )
        except Exception:
            pass

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


@router.get("/board", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_board(
    *,
    db: Session = Depends(deps.get_db),
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    pm_id: Optional[int] = Query(None, description="项目经理ID筛选"),
    health: Optional[str] = Query(None, description="健康度筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目看板视图 - 按阶段分组展示项目
    """
    query = db.query(Project).filter(Project.is_active == True)

    # 应用数据权限过滤
    from app.services.data_scope_service import DataScopeService
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    if project_type:
        query = query.filter(Project.project_type == project_type)
    if pm_id:
        query = query.filter(Project.pm_id == pm_id)
    if health:
        query = query.filter(Project.health == health)

    projects = query.all()

    # 按阶段分组
    stages = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    stage_names = {
        'S1': '需求进入',
        'S2': '需求澄清',
        'S3': '立项评审',
        'S4': '方案设计',
        'S5': '采购制造',
        'S6': '装配联调',
        'S7': '出厂验收',
        'S8': '现场交付',
        'S9': '质保结项',
    }

    board = {}
    for stage in stages:
        board[stage] = {
            'stage': stage,
            'stage_name': stage_names.get(stage, stage),
            'projects': [],
            'count': 0,
            'total_contract_amount': 0,
        }

    for project in projects:
        stage = project.stage or 'S1'
        if stage in board:
            board[stage]['projects'].append({
                'id': project.id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'customer_name': project.customer_name,
                'pm_name': project.pm_name,
                'health': project.health,
                'progress_pct': project.progress_pct,
                'contract_amount': float(project.contract_amount or 0),
                'planned_end_date': project.planned_end_date.isoformat() if project.planned_end_date else None,
            })
            board[stage]['count'] += 1
            board[stage]['total_contract_amount'] += float(project.contract_amount or 0)

    return ResponseModel(
        code=200,
        message="success",
        data={
            'stages': stages,
            'board': board,
            'total_projects': len(projects),
        }
    )


@router.get("/stats", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_stats(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目统计数据
    """
    query = db.query(Project).filter(Project.is_active == True)

    # 应用数据权限过滤
    from app.services.data_scope_service import DataScopeService
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    if start_date:
        query = query.filter(Project.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Project.created_at <= datetime.combine(end_date, datetime.max.time()))

    projects = query.all()

    # 统计数据
    total_count = len(projects)
    total_contract_amount = sum(float(p.contract_amount or 0) for p in projects)

    # 按阶段统计
    stage_stats = {}
    for project in projects:
        stage = project.stage or 'S1'
        if stage not in stage_stats:
            stage_stats[stage] = {'count': 0, 'amount': 0}
        stage_stats[stage]['count'] += 1
        stage_stats[stage]['amount'] += float(project.contract_amount or 0)

    # 按健康度统计
    health_stats = {}
    for project in projects:
        health = project.health or 'H1'
        if health not in health_stats:
            health_stats[health] = {'count': 0, 'amount': 0}
        health_stats[health]['count'] += 1
        health_stats[health]['amount'] += float(project.contract_amount or 0)

    # 按项目类型统计
    type_stats = {}
    for project in projects:
        ptype = project.project_type or 'OTHER'
        if ptype not in type_stats:
            type_stats[ptype] = {'count': 0, 'amount': 0}
        type_stats[ptype]['count'] += 1
        type_stats[ptype]['amount'] += float(project.contract_amount or 0)

    return ResponseModel(
        code=200,
        message="success",
        data={
            'total_count': total_count,
            'total_contract_amount': total_contract_amount,
            'by_stage': stage_stats,
            'by_health': health_stats,
            'by_type': type_stats,
        }
    )


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def read_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    use_cache: bool = Query(True, description="是否使用缓存"),
) -> Any:
    """
    Get project by ID.
    """
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
            pass

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
        pass

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
        pass

    return ResponseModel(
        code=200,
        message="项目删除成功",
        data={"id": project_id}
    )


@router.post("/{project_id}/clone", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def clone_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    clone_request: ProjectCloneRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    克隆项目
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    source_project = check_project_access_or_raise(db, current_user, project_id, "您没有权限克隆该项目")

    # 检查项目编码是否已存在
    existing = db.query(Project).filter(Project.project_code == clone_request.project_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="项目编码已存在")

    # 创建新项目
    new_project = Project(
        project_code=clone_request.project_code,
        project_name=clone_request.project_name,
        project_type=source_project.project_type,
        customer_id=source_project.customer_id,
        customer_name=source_project.customer_name,
        customer_contact=source_project.customer_contact,
        customer_phone=source_project.customer_phone,
        pm_id=current_user.id,
        pm_name=current_user.real_name or current_user.username,
        stage='S1',
        status='ST01',
        health='H1',
        description=source_project.description,
        requirements=source_project.requirements,
        budget_amount=source_project.budget_amount,
        is_active=True,
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # 克隆机台（如果需要）
    if clone_request.clone_machines:
        source_machines = db.query(Machine).filter(Machine.project_id == project_id).all()
        for source_machine in source_machines:
            new_machine = Machine(
                project_id=new_project.id,
                machine_code=source_machine.machine_code,
                machine_name=source_machine.machine_name,
                machine_type=source_machine.machine_type,
                status='PENDING',
                progress_pct=0,
            )
            db.add(new_machine)

    # 克隆里程碑（如果需要）
    if clone_request.clone_milestones:
        source_milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id
        ).all()
        for source_milestone in source_milestones:
            new_milestone = ProjectMilestone(
                project_id=new_project.id,
                milestone_name=source_milestone.milestone_name,
                milestone_type=source_milestone.milestone_type,
                stage=source_milestone.stage,
                is_key=source_milestone.is_key,
            )
            db.add(new_milestone)

    # 初始化标准阶段
    from app.utils.project_utils import init_project_stages
    init_project_stages(db, new_project.id)

    db.commit()

    return ResponseModel(
        code=200,
        message="项目克隆成功",
        data={
            "id": new_project.id,
            "project_code": new_project.project_code,
            "project_name": new_project.project_name,
            "source_project_id": project_id,
        }
    )
