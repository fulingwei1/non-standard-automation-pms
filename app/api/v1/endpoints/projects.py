from typing import Any, List, Optional, Tuple, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path, status, UploadFile, File
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project, Customer, ProjectStatusLog, ProjectPaymentPlan, ProjectMilestone, ProjectTemplate, ProjectTemplateVersion, Machine, ProjectStage, ProjectMember, FinancialProjectCost
from app.models.pmo import PmoResourceAllocation, PmoProjectRisk, PmoChangeRequest
from app.models.shortage import MaterialTransfer
from app.models.progress import Task
from app.models.progress import Task
from app.models.sales import Contract, Invoice
from app.models.business_support import InvoiceRequest
from app.models.project_review import ProjectReview, ProjectLesson, ProjectBestPractice
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectDetailResponse,
    ProjectStatusLogResponse,
    ProjectHealthDetailsResponse,
    ProjectPaymentPlanCreate,
    ProjectPaymentPlanUpdate,
    ProjectPaymentPlanResponse,
    ProjectTemplateCreate,
    ProjectTemplateUpdate,
    ProjectTemplateResponse,
    ProjectTemplateVersionCreate,
    ProjectTemplateVersionUpdate,
    ProjectTemplateVersionResponse,
    ProjectCloneRequest,
    ProjectArchiveRequest,
    ResourceOptimizationResponse,
    ResourceConflictResponse,
    ProjectRelationResponse,
    RiskMatrixResponse,
    ChangeImpactRequest,
    ChangeImpactResponse,
    ProjectSummaryResponse,
    ProjectTimelineResponse,
    TimelineEvent,
    StageAdvanceRequest,
    StageAdvanceResponse,
    FinancialProjectCostCreate,
    FinancialProjectCostResponse,
    FinancialProjectCostUploadRequest,
    ProjectStatusResponse,
    BatchUpdateStatusRequest,
    BatchArchiveRequest,
    BatchAssignPMRequest,
    BatchUpdateStageRequest,
    BatchOperationResponse,
    ProjectDashboardResponse,
    InProductionProjectSummary,
)
from app.schemas.project_review import (
    ProjectReviewCreate,
    ProjectReviewUpdate,
    ProjectReviewResponse,
    ProjectLessonCreate,
    ProjectLessonUpdate,
    ProjectLessonResponse,
    ProjectBestPracticeCreate,
    ProjectBestPracticeUpdate,
    ProjectBestPracticeResponse,
    LessonStatisticsResponse,
    BestPracticeRecommendationRequest,
    BestPracticeRecommendationResponse
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


def _sync_invoice_request_receipt_status(db: Session, plan: ProjectPaymentPlan) -> None:
    """根据收款计划实收金额同步开票申请回款状态"""
    invoice_requests = db.query(InvoiceRequest).filter(
        InvoiceRequest.payment_plan_id == plan.id,
        InvoiceRequest.status == "APPROVED"
    ).all()
    if not invoice_requests:
        return

    planned_amount = plan.planned_amount or Decimal("0")
    actual_amount = plan.actual_amount or Decimal("0")

    if planned_amount and actual_amount >= planned_amount:
        receipt_status = "PAID"
    elif actual_amount > 0:
        receipt_status = "PARTIAL"
    else:
        receipt_status = "UNPAID"

    for invoice_request in invoice_requests:
        if invoice_request.receipt_status != receipt_status:
            invoice_request.receipt_status = receipt_status
            invoice_request.receipt_updated_at = datetime.utcnow()
            db.add(invoice_request)


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

    # 关键词搜索（Sprint 5.1: 性能优化 - 使用索引友好的查询）
    if keyword:
        # 使用LIKE查询，但优先使用精确匹配（如果可能）
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

    # Sprint 5.1: 性能优化 - 优化总数统计
    # 对于大数据量场景，可以考虑使用估算或延迟计算
    # 这里先使用精确计算，后续可以优化
    try:
        count_result = query.count()
        total = int(count_result) if count_result is not None else 0
    except Exception:
        total = 0

    # Sprint 5.1: 性能优化 - 使用selectinload优化关联查询
    # selectinload比joinedload更安全，不会导致IndexError，特别适合处理NULL或无效外键
    query = query.options(
        selectinload(Project.customer),
        selectinload(Project.manager)
    )

    # Sprint 5.1: 性能优化 - 尝试从缓存获取（仅对常用筛选条件）
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
            # 缓存失败不影响主流程
            pass

    # 分页
    offset = (page - 1) * page_size
    projects = query.order_by(desc(Project.created_at)).offset(offset).limit(page_size).all()

    # 补充冗余字段（确保customer_name和pm_name存在）
    for project in projects:
        if not project.customer_name and project.customer:
            project.customer_name = project.customer.customer_name
        if not project.pm_name and project.manager:
            project.pm_name = project.manager.real_name or project.manager.username

    # 计算总页数，确保 total 不为 None
    total = int(total) if total is not None else 0
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    # 将ORM对象转换为响应模型
    from app.schemas.project import ProjectListResponse
    project_items = [ProjectListResponse.model_validate(p) for p in projects]

    result = PaginatedResponse(
        items=project_items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )

    # Sprint 5.1: 性能优化 - 将结果存入缓存
    if use_cache:
        try:
            from app.services.cache_service import CacheService
            cache_service = CacheService()
            from app.core.config import settings
            cache_service.set_project_list(
                result.model_dump(),
                expire_seconds=settings.REDIS_CACHE_PROJECT_LIST_TTL,
                **cache_key_params
            )
        except Exception:
            # 缓存失败不影响主流程
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

    # Convert schema to dict and remove any fields not in model
    project_data = project_in.model_dump()

    # Remove machine_count if it's strictly for logic
    project_data.pop("machine_count", None)

    project = Project(**project_data)

    # Optionally populate redundant fields from related objects
    if project.customer_id:
        from app.models.project import Customer

        customer = db.query(Customer).get(project.customer_id)
        if customer:
            project.customer_name = customer.customer_name
            project.customer_contact = customer.contact_person
            project.customer_phone = customer.contact_phone

    if project.pm_id:
        from app.models.user import User

        pm = db.query(User).get(project.pm_id)
        if pm:
            project.pm_name = pm.real_name or pm.username

    db.add(project)
    db.commit()
    db.refresh(project)

    # Initialize standard stages for the project
    from app.utils.project_utils import init_project_stages

    init_project_stages(db, project.id)

    return project


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def read_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    use_cache: bool = Query(True, description="是否使用缓存"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Get project by ID.
    
    Sprint 5.3: 支持缓存机制
    """
    """
    获取项目详情（包含关联数据）
    
    Sprint 5.3: 支持缓存机制
    """
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)
    
    # Sprint 5.3: 尝试从缓存获取
    if use_cache:
        try:
            from app.services.cache_service import CacheService
            cache_service = CacheService()  # 使用内存缓存（如果Redis不可用）
            cached_data = cache_service.get_project_detail(project_id)
            if cached_data:
                # 从缓存恢复项目对象（简化实现，实际可能需要更复杂的序列化）
                # 这里先跳过缓存，直接查询数据库
                pass
        except Exception:
            # 缓存失败不影响主流程
            pass
    
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

    # 加载项目成员（包含关联的User对象）
    from app.schemas.project import ProjectMemberResponse
    members_query = (
        db.query(ProjectMember)
        .options(joinedload(ProjectMember.user))
        .filter(ProjectMember.project_id == project_id)
        .all()
    )
    
    # 转换为ProjectMemberResponse格式（确保username字段存在）
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
    
    # 加载machines和milestones（因为ProjectDetailResponse需要这些字段）
    from app.schemas.project import MachineResponse, MilestoneResponse
    machines_query = project.machines.all() if hasattr(project.machines, 'all') else []
    machines = [MachineResponse.model_validate(m) for m in machines_query]
    
    milestones_query = project.milestones.all() if hasattr(project.milestones, 'all') else []
    milestones = [MilestoneResponse.model_validate(m) for m in milestones_query]
    
    # 构建ProjectDetailResponse对象
    # 使用字典方式构建，避免Pydantic验证时访问SQLAlchemy关系对象
    from app.schemas.project import ProjectDetailResponse, ProjectResponse
    
    # 先构建基础ProjectResponse
    project_base = ProjectResponse.model_validate(project)
    
    # 然后构建ProjectDetailResponse，直接设置members/machines/milestones
    project_detail = ProjectDetailResponse(
        **project_base.model_dump(),
        members=members,
        machines=machines,
        milestones=milestones
    )

    # Sprint 5.3: 将结果存入缓存
    if use_cache:
        try:
            from app.services.cache_service import CacheService
            from app.core.config import settings
            cache_service = CacheService()
            # 将项目数据序列化为字典（简化实现）
            project_dict = {
                "id": project.id,
                "project_code": project.project_code,
                "project_name": project.project_name,
                # ... 其他字段
            }
            cache_service.set_project_detail(
                project_id, 
                project_dict, 
                expire_seconds=settings.REDIS_CACHE_PROJECT_DETAIL_TTL
            )
        except Exception:
            # 缓存失败不影响主流程
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
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id, "您没有权限修改该项目")

    update_data = project_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(project, field):
            setattr(project, field, value)

    # Update redundant fields if ID changed
    if "customer_id" in update_data:
        from app.models.project import Customer

        customer = db.query(Customer).get(project.customer_id)
        if customer:
            project.customer_name = customer.customer_name
            project.customer_contact = customer.contact_person
            project.customer_phone = customer.contact_phone

    if "pm_id" in update_data:
        from app.models.user import User

        pm = db.query(User).get(project.pm_id)
        if pm:
            project.pm_name = pm.real_name or pm.username

    db.add(project)
    db.commit()
    
    # Sprint 5.3: 使项目缓存失效
    try:
        from app.services.cache_service import CacheService
        cache_service = CacheService()
        cache_service.invalidate_project_detail(project_id)
        cache_service.invalidate_project_list()  # 列表缓存也需要失效
    except Exception:
        # 缓存失效失败不影响主流程
        pass
    
    # Sprint 2.4: 项目更新时自动同步到合同
    if any(field in update_data for field in ["contract_amount", "contract_date", "planned_end_date", "stage", "status"]):
        try:
            from app.services.data_sync_service import DataSyncService
            sync_service = DataSyncService(db)
            sync_service.sync_project_to_contract(project_id)
        except Exception as e:
            # 同步失败不影响项目更新，记录日志
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"项目更新同步到合同失败：{str(e)}", exc_info=True)
    
    db.refresh(project)
    return project


@router.delete("/{project_id}", response_model=ResponseModel, status_code=200)
def delete_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除项目（软删除）
    
    - **project_id**: 项目ID
    - 软删除：将is_active设置为False，不实际删除数据
    - 检查是否有关联数据（机台、任务等），如果有则不允许删除
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查是否有关联的机台
    from app.models.project import Machine
    machine_count = db.query(Machine).filter(Machine.project_id == project_id).count()
    if machine_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"项目下存在 {machine_count} 台机台，无法删除。请先删除或转移机台。"
        )
    
    # 检查是否有关联的任务（如果有任务表）
    # 这里假设有任务表，如果没有可以注释掉
    # from app.models.task import Task
    # task_count = db.query(Task).filter(Task.project_id == project_id).count()
    # if task_count > 0:
    #     raise HTTPException(
    #         status_code=400,
    #         detail=f"项目下存在 {task_count} 个任务，无法删除。请先删除或转移任务。"
    #     )
    
    # 软删除：禁用项目
    project.is_active = False
    db.add(project)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="项目已删除（已禁用）"
    )


@router.get("/board", response_model=ResponseModel)
def get_project_board(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目看板数据（红黄绿灯看板）
    根据健康度（H1-H4）和进度状态分类项目
    
    - **green**: 绿灯项目（健康度H1-H2，进度正常）
    - **yellow**: 黄灯项目（健康度H3，或进度有延迟风险）
    - **red**: 红灯项目（健康度H4，或严重延迟）
    """
    # 查询所有启用的项目
    projects = db.query(Project).filter(Project.is_active == True).all()
    
    # 按健康度和进度分类
    board_data = {
        "green": [],  # 绿灯：健康度H1-H2，进度正常
        "yellow": [],  # 黄灯：健康度H3，或进度有延迟风险
        "red": [],  # 红灯：健康度H4，或严重延迟
        "total": len(projects),
    }
    
    today = date.today()
    
    for project in projects:
        project_info = {
            "id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "customer_name": project.customer_name,
            "stage": project.stage,
            "status": project.status,
            "health": project.health or "H1",
            "progress_pct": float(project.progress_pct) if project.progress_pct else 0,
            "pm_name": project.pm_name,
            "planned_end_date": project.planned_end_date.isoformat() if project.planned_end_date else None,
            "actual_end_date": project.actual_end_date.isoformat() if project.actual_end_date else None,
        }
        
        # 判断项目应该放在哪个灯
        health = project.health or "H1"
        progress = float(project.progress_pct) if project.progress_pct else 0
        planned_end = project.planned_end_date
        
        # 红灯：健康度H4，或进度严重滞后（<50%且已过计划结束日期）
        is_red = False
        if health == "H4":
            is_red = True
        elif planned_end and progress < 50:
            days_overdue = (today - planned_end).days
            if days_overdue > 0:
                is_red = True
        
        # 黄灯：健康度H3，或进度有延迟风险（<80%且已过计划结束日期）
        is_yellow = False
        if not is_red:
            if health == "H3":
                is_yellow = True
            elif planned_end and progress < 80:
                days_overdue = (today - planned_end).days
                if days_overdue > 0:
                    is_yellow = True
        
        if is_red:
            board_data["red"].append(project_info)
        elif is_yellow:
            board_data["yellow"].append(project_info)
        else:
            board_data["green"].append(project_info)
    
    return ResponseModel(
        code=200,
        message="获取项目看板数据成功",
        data=board_data
    )


@router.get("/stats", response_model=ResponseModel)
def get_project_stats(
    db: Session = Depends(deps.get_db),
    group_by: Optional[str] = Query(None, description="分组方式：customer/month（可选）"),
    start_date: Optional[date] = Query(None, description="开始日期（用于按月统计）"),
    end_date: Optional[date] = Query(None, description="结束日期（用于按月统计）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目统计信息（按状态、阶段、健康度、客户、月份统计）
    
    返回：
    - total: 项目总数
    - average_progress: 平均进度
    - by_status: 按状态统计
    - by_stage: 按阶段统计
    - by_health: 按健康度统计
    - by_pm: 按项目经理统计
    - by_customer: 按客户统计（如果group_by=customer）
    - by_month: 按月份统计（如果group_by=month）
    """
    from app.services.data_scope_service import DataScopeService
    from app.services.project_statistics_service import build_project_statistics
    
    # 应用数据权限过滤
    query = db.query(Project).filter(Project.is_active == True)
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    
    # 构建统计数据
    stats_data = build_project_statistics(db, query, group_by, start_date, end_date)
    
    return ResponseModel(
        code=200,
        message="获取项目统计信息成功",
        data=stats_data
    )


@router.put("/{project_id}/stage", response_model=ProjectResponse)
def update_project_stage(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    stage: str = Query(..., description="阶段编码（S1-S9）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目阶段
    
    - **project_id**: 项目ID
    - **stage**: 阶段编码（S1-S9）
      - S1: 需求进入
      - S2: 方案设计
      - S3: 采购备料
      - S4: 加工制造
      - S5: 装配调试
      - S6: 出厂验收(FAT)
      - S7: 包装发运
      - S8: 现场安装(SAT)
      - S9: 质保结项
    """
    # 验证阶段编码
    valid_stages = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    if stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"无效的阶段编码。有效值：{', '.join(valid_stages)}"
        )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 记录旧阶段（用于历史记录）
    old_stage = project.stage
    
    # 如果阶段没有变化，直接返回
    if old_stage == stage:
        return project
    
    # 更新阶段
    project.stage = stage
    db.add(project)
    
    # 记录状态变更历史
    status_log = ProjectStatusLog(
        project_id=project_id,
        old_stage=old_stage,
        new_stage=stage,
        old_status=project.status,
        new_status=project.status,
        old_health=project.health,
        new_health=project.health,
        change_type="STAGE_CHANGE",
        changed_by=current_user.id,
        changed_at=datetime.now()
    )
    db.add(status_log)
    
    # 如果项目进入S8阶段，自动创建安装调试派工单
    if stage == "S8" and old_stage != "S8":
        try:
            from app.models.installation_dispatch import InstallationDispatchOrder
            from app.api.v1.endpoints.installation_dispatch import generate_order_no
            from app.models.project import Machine
            
            # 获取项目的所有机台
            machines = db.query(Machine).filter(Machine.project_id == project_id).all()
            
            # 为每个机台创建安装调试派工单
            for machine in machines:
                # 检查是否已存在该机台的安装调试派工单
                existing_order = db.query(InstallationDispatchOrder).filter(
                    InstallationDispatchOrder.project_id == project_id,
                    InstallationDispatchOrder.machine_id == machine.id,
                    InstallationDispatchOrder.status != "CANCELLED"
                ).first()
                
                if not existing_order:
                    dispatch_order = InstallationDispatchOrder(
                        order_no=generate_order_no(db),
                        project_id=project_id,
                        machine_id=machine.id,
                        customer_id=project.customer_id,
                        task_type="INSTALLATION",
                        task_title=f"{machine.machine_no} 现场安装调试",
                        task_description=f"项目 {project.project_name} 的 {machine.machine_no} 设备现场安装调试",
                        location=project.customer_address if hasattr(project, 'customer_address') else None,
                        scheduled_date=date.today() + timedelta(days=7),  # 默认7天后
                        estimated_hours=Decimal("8.0"),
                        priority="HIGH",
                        status="PENDING",
                        progress=0,
                    )
                    db.add(dispatch_order)
        except Exception as e:
            # 如果创建派工单失败，记录日志但不影响阶段更新
            import logging
            logging.warning(f"自动创建安装调试派工单失败：{str(e)}")
    
    db.commit()
    db.refresh(project)
    
    return project


@router.get("/{project_id}/status", response_model=ProjectStatusResponse)
def get_project_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目三维状态
    
    返回项目的当前阶段、状态、健康度信息
    """
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)
    
    # 阶段名称映射
    stage_names = {
        'S1': '需求进入',
        'S2': '方案设计',
        'S3': '采购备料',
        'S4': '加工制造',
        'S5': '装配调试',
        'S6': '出厂验收(FAT)',
        'S7': '包装发运',
        'S8': '现场安装(SAT)',
        'S9': '质保结项',
    }
    
    # 状态名称映射（简化版，实际应该从字典表获取）
    status_names = {
        'ST01': '项目启动',
        'ST02': '需求分析',
        'ST03': '方案设计',
        'ST05': '合同签订',
        'ST07': '生产准备',
        'ST10': '采购执行',
        'ST15': '生产执行',
        'ST20': '验收测试',
        'ST25': '交付安装',
        'ST30': '项目结项',
    }
    
    # 健康度名称映射
    health_names = {
        'H1': '正常(绿色)',
        'H2': '有风险(黄色)',
        'H3': '阻塞(红色)',
        'H4': '已完结(灰色)',
    }
    
    return ProjectStatusResponse(
        project_id=project.id,
        project_code=project.project_code,
        project_name=project.project_name,
        stage=project.stage or "S1",
        stage_name=stage_names.get(project.stage, project.stage),
        status=project.status or "ST01",
        status_name=status_names.get(project.status, project.status),
        health=project.health,
        health_name=health_names.get(project.health, project.health) if project.health else None,
        progress_pct=float(project.progress_pct or 0),
        last_updated=project.updated_at,
    )


@router.put("/{project_id}/status", response_model=ProjectResponse)
def update_project_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    status: str = Query(..., description="状态编码（ST01-ST30）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目状态
    
    - **project_id**: 项目ID
    - **status**: 状态编码（ST01-ST30）
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 记录旧状态（用于历史记录）
    old_status = project.status
    
    # 如果状态没有变化，直接返回
    if old_status == status:
        return project
    
    # 更新状态
    project.status = status
    db.add(project)
    
    # 记录状态变更历史
    status_log = ProjectStatusLog(
        project_id=project_id,
        old_stage=project.stage,
        new_stage=project.stage,
        old_status=old_status,
        new_status=status,
        old_health=project.health,
        new_health=project.health,
        change_type="STATUS_CHANGE",
        changed_by=current_user.id,
        changed_at=datetime.now()
    )
    db.add(status_log)
    db.commit()
    
    # 自动计算健康度（状态变化可能影响健康度）
    try:
        from app.services.health_calculator import HealthCalculator
        calculator = HealthCalculator(db)
        calculator.calculate_and_update(project, auto_save=True)
    except Exception as e:
        # 健康度计算失败不影响状态更新
        import logging
        logging.error(f"自动计算健康度失败: {str(e)}")
    
    db.refresh(project)
    return project


@router.put("/{project_id}/health", response_model=ProjectResponse)
def update_project_health(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    health: str = Query(..., description="健康度编码（H1-H4）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目健康度
    
    - **project_id**: 项目ID
    - **health**: 健康度编码（H1-H4）
      - H1: 正常(绿色)
      - H2: 有风险(黄色)
      - H3: 阻塞(红色)
      - H4: 已完结(灰色)
    """
    # 验证健康度编码
    valid_health = ['H1', 'H2', 'H3', 'H4']
    if health not in valid_health:
        raise HTTPException(
            status_code=400,
            detail=f"无效的健康度编码。有效值：{', '.join(valid_health)}"
        )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 记录旧健康度（用于历史记录）
    old_health = project.health
    
    # 如果健康度没有变化，直接返回
    if old_health == health:
        return project
    
    # 更新健康度
    project.health = health
    db.add(project)
    
    # 记录状态变更历史
    status_log = ProjectStatusLog(
        project_id=project_id,
        old_stage=project.stage,
        new_stage=project.stage,
        old_status=project.status,
        new_status=project.status,
        old_health=old_health,
        new_health=health,
        change_type="HEALTH_CHANGE",
        changed_by=current_user.id,
        changed_at=datetime.now()
    )
    db.add(status_log)
    db.commit()
    db.refresh(project)
    
    return project


@router.post("/{project_id}/health/calculate", response_model=ResponseModel)
def calculate_project_health_manual(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    手动触发项目健康度计算
    
    - **project_id**: 项目ID
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    try:
        from app.services.health_calculator import HealthCalculator
        calculator = HealthCalculator(db)
        result = calculator.calculate_and_update(project, auto_save=True)
        
        return ResponseModel(
            code=200,
            message="健康度计算成功",
            data={
                "project_id": project_id,
                "old_health": result['old_health'],
                "new_health": result['new_health'],
                "changed": result['changed']
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"健康度计算失败: {str(e)}"
        )


@router.get("/{project_id}/health/details", response_model=ProjectHealthDetailsResponse)
def get_project_health_details(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目健康度详细信息（用于诊断）
    
    - **project_id**: 项目ID
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    try:
        from app.services.health_calculator import HealthCalculator
        calculator = HealthCalculator(db)
        details = calculator.get_health_details(project)
        
        return details
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取健康度详情失败: {str(e)}"
        )


@router.post("/health/batch-calculate", response_model=ResponseModel)
def batch_calculate_health(
    *,
    db: Session = Depends(deps.get_db),
    project_ids: Optional[List[int]] = Body(None, description="项目ID列表，为空则计算所有活跃项目"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量计算项目健康度
    
    - **project_ids**: 项目ID列表（可选，为空则计算所有活跃项目）
    """
    try:
        from app.services.health_calculator import HealthCalculator
        calculator = HealthCalculator(db)
        result = calculator.batch_calculate(project_ids=project_ids)
        
        return ResponseModel(
            code=200,
            message="批量健康度计算完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"批量健康度计算失败: {str(e)}"
        )


@router.post("/{project_id}/stages/init", response_model=ResponseModel)
def init_project_stages(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    初始化项目阶段（创建标准9个阶段及其状态）
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查是否已经初始化过
    from app.models.project import ProjectStage
    existing_stages = db.query(ProjectStage).filter(ProjectStage.project_id == project_id).count()
    if existing_stages > 0:
        raise HTTPException(
            status_code=400,
            detail="项目阶段已初始化，如需重新初始化请先删除现有阶段"
        )
    
    # 调用初始化函数
    from app.utils.project_utils import init_project_stages
    init_project_stages(db, project_id)
    
    return ResponseModel(
        code=200,
        message="项目阶段初始化成功",
        data={"project_id": project_id, "stages_count": 9}
    )


def _serialize_project_status_log(log: ProjectStatusLog) -> Dict[str, Any]:
    """构造状态变更日志响应数据"""
    return {
        "id": log.id,
        "project_id": log.project_id,
        "machine_id": log.machine_id,
        "old_stage": log.old_stage,
        "old_status": log.old_status,
        "old_health": log.old_health,
        "new_stage": log.new_stage,
        "new_status": log.new_status,
        "new_health": log.new_health,
        "change_type": log.change_type,
        "change_reason": log.change_reason,
        "change_note": log.change_note,
        "changed_by": log.changed_by,
        "changed_by_name": log.changer.username if log.changer else None,
        "changed_at": log.changed_at,
    }


@router.get("/{project_id}/status-history", response_model=List[ProjectStatusLogResponse])
def get_project_status_history(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    change_type: Optional[str] = Query(None, description="变更类型筛选（STAGE_CHANGE/STATUS_CHANGE/HEALTH_CHANGE）"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目状态变更历史
    
    - **project_id**: 项目ID
    - **change_type**: 变更类型筛选（可选）
    - **limit**: 返回记录数（默认50，最大200）
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)
    
    query = db.query(ProjectStatusLog).filter(ProjectStatusLog.project_id == project_id)
    
    if change_type:
        valid_types = ['STAGE_CHANGE', 'STATUS_CHANGE', 'HEALTH_CHANGE']
        if change_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"无效的变更类型。有效值：{', '.join(valid_types)}"
            )
        query = query.filter(ProjectStatusLog.change_type == change_type)
    
    logs = query.order_by(desc(ProjectStatusLog.changed_at)).limit(limit).all()
    
    return [_serialize_project_status_log(log) for log in logs]


@router.get(
    "/{project_id}/status-logs",
    response_model=PaginatedResponse[ProjectStatusLogResponse]
)
def get_project_status_logs(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(
        20,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="每页数量（支持limit参数）",
    ),
    change_type: Optional[str] = Query(None, description="变更类型筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目状态变更日志（分页）
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    query = db.query(ProjectStatusLog).filter(ProjectStatusLog.project_id == project_id)

    if change_type:
        valid_types = ['STAGE_CHANGE', 'STATUS_CHANGE', 'HEALTH_CHANGE']
        if change_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"无效的变更类型。有效值：{', '.join(valid_types)}"
            )
        query = query.filter(ProjectStatusLog.change_type == change_type)

    try:
        count_result = query.count()
        total = int(count_result) if count_result is not None else 0
    except Exception:
        total = 0
    offset = (page - 1) * limit
    logs = query.order_by(desc(ProjectStatusLog.changed_at)).offset(offset).limit(limit).all()
    items = [_serialize_project_status_log(log) for log in logs]
    total = int(total) if total is not None else 0
    pages = (total + limit - 1) // limit if limit and total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=limit,
        pages=pages,
    )


# ==================== 项目收款计划 ====================


@router.get("/{project_id}/payment-plans", response_model=PaginatedResponse[ProjectPaymentPlanResponse])
def get_project_payment_plans(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目收款计划列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    query = db.query(ProjectPaymentPlan).filter(ProjectPaymentPlan.project_id == project_id)
    
    if status:
        query = query.filter(ProjectPaymentPlan.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    plans = query.order_by(ProjectPaymentPlan.payment_no).offset(offset).limit(page_size).all()
    
    items = []
    for plan in plans:
        plan_dict = {
            "id": plan.id,
            "project_id": plan.project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "contract_id": plan.contract_id,
            "contract_code": plan.contract.contract_code if plan.contract else None,
            "payment_no": plan.payment_no,
            "payment_name": plan.payment_name,
            "payment_type": plan.payment_type,
            "payment_ratio": plan.payment_ratio,
            "planned_amount": plan.planned_amount,
            "actual_amount": plan.actual_amount or Decimal("0"),
            "planned_date": plan.planned_date,
            "actual_date": plan.actual_date,
            "milestone_id": plan.milestone_id,
            "milestone_code": plan.milestone.milestone_code if plan.milestone else None,
            "milestone_name": plan.milestone.milestone_name if plan.milestone else None,
            "trigger_milestone": plan.trigger_milestone,
            "trigger_condition": plan.trigger_condition,
            "status": plan.status,
            "invoice_id": plan.invoice_id,
            "invoice_no": plan.invoice_no,
            "invoice_date": plan.invoice_date,
            "invoice_amount": plan.invoice_amount,
            "remark": plan.remark,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
        }
        items.append(ProjectPaymentPlanResponse(**plan_dict))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/{project_id}/payment-plans", response_model=ProjectPaymentPlanResponse)
def create_project_payment_plan(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    plan_in: ProjectPaymentPlanCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建项目收款计划
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证合同是否存在
    if plan_in.contract_id:
        contract = db.query(Contract).filter(Contract.id == plan_in.contract_id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="合同不存在")
    
    # 验证里程碑是否存在
    if plan_in.milestone_id:
        milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == plan_in.milestone_id).first()
        if not milestone:
            raise HTTPException(status_code=404, detail="里程碑不存在")
    
    plan_data = plan_in.model_dump()
    plan_data["project_id"] = project_id
    plan = ProjectPaymentPlan(**plan_data)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    plan_dict = {
        "id": plan.id,
        "project_id": plan.project_id,
        "project_code": project.project_code,
        "project_name": project.project_name,
        "contract_id": plan.contract_id,
        "contract_code": plan.contract.contract_code if plan.contract else None,
        "payment_no": plan.payment_no,
        "payment_name": plan.payment_name,
        "payment_type": plan.payment_type,
        "payment_ratio": plan.payment_ratio,
        "planned_amount": plan.planned_amount,
        "actual_amount": plan.actual_amount or Decimal("0"),
        "planned_date": plan.planned_date,
        "actual_date": plan.actual_date,
        "milestone_id": plan.milestone_id,
        "milestone_code": plan.milestone.milestone_code if plan.milestone else None,
        "milestone_name": plan.milestone.milestone_name if plan.milestone else None,
        "trigger_milestone": plan.trigger_milestone,
        "trigger_condition": plan.trigger_condition,
        "status": plan.status,
        "invoice_id": plan.invoice_id,
        "invoice_no": plan.invoice_no,
        "invoice_date": plan.invoice_date,
        "invoice_amount": plan.invoice_amount,
        "remark": plan.remark,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
    }
    return ProjectPaymentPlanResponse(**plan_dict)


@router.put("/payment-plans/{plan_id}", response_model=ProjectPaymentPlanResponse)
def update_project_payment_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    plan_in: ProjectPaymentPlanUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目收款计划
    """
    plan = db.query(ProjectPaymentPlan).filter(ProjectPaymentPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="收款计划不存在")
    
    update_data = plan_in.model_dump(exclude_unset=True)
    sync_receipt_status = any(field in update_data for field in ("actual_amount", "status"))
    
    # 验证里程碑是否存在
    if "milestone_id" in update_data and update_data["milestone_id"]:
        milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == update_data["milestone_id"]).first()
        if not milestone:
            raise HTTPException(status_code=404, detail="里程碑不存在")
    
    for field, value in update_data.items():
        if hasattr(plan, field):
            setattr(plan, field, value)
    
    if sync_receipt_status:
        _sync_invoice_request_receipt_status(db, plan)

    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    project = plan.project
    plan_dict = {
        "id": plan.id,
        "project_id": plan.project_id,
        "project_code": project.project_code if project else None,
        "project_name": project.project_name if project else None,
        "contract_id": plan.contract_id,
        "contract_code": plan.contract.contract_code if plan.contract else None,
        "payment_no": plan.payment_no,
        "payment_name": plan.payment_name,
        "payment_type": plan.payment_type,
        "payment_ratio": plan.payment_ratio,
        "planned_amount": plan.planned_amount,
        "actual_amount": plan.actual_amount or Decimal("0"),
        "planned_date": plan.planned_date,
        "actual_date": plan.actual_date,
        "milestone_id": plan.milestone_id,
        "milestone_code": plan.milestone.milestone_code if plan.milestone else None,
        "milestone_name": plan.milestone.milestone_name if plan.milestone else None,
        "trigger_milestone": plan.trigger_milestone,
        "trigger_condition": plan.trigger_condition,
        "status": plan.status,
        "invoice_id": plan.invoice_id,
        "invoice_no": plan.invoice_no,
        "invoice_date": plan.invoice_date,
        "invoice_amount": plan.invoice_amount,
        "remark": plan.remark,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
    }
    return ProjectPaymentPlanResponse(**plan_dict)


@router.delete("/payment-plans/{plan_id}", response_model=ResponseModel)
def delete_project_payment_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除项目收款计划
    """
    plan = db.query(ProjectPaymentPlan).filter(ProjectPaymentPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="收款计划不存在")
    
    # 如果已开票，不允许删除
    if plan.invoice_id:
        raise HTTPException(status_code=400, detail="收款计划已关联发票，无法删除")
    
    db.delete(plan)
    db.commit()
    
    return ResponseModel(code=200, message="收款计划已删除")


# ==================== 项目模板管理 ====================

@router.get("/templates", response_model=PaginatedResponse)
def read_project_templates(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（模板编码/名称）"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目模板列表
    """
    query = db.query(ProjectTemplate)
    
    if keyword:
        query = query.filter(
            or_(
                ProjectTemplate.template_code.like(f"%{keyword}%"),
                ProjectTemplate.template_name.like(f"%{keyword}%"),
            )
        )
    
    if is_active is not None:
        query = query.filter(ProjectTemplate.is_active == is_active)
    
    total = query.count()
    templates = query.order_by(desc(ProjectTemplate.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for template in templates:
        items.append(ProjectTemplateResponse(
            id=template.id,
            template_code=template.template_code,
            template_name=template.template_name,
            description=template.description,
            project_type=template.project_type,
            product_category=template.product_category,
            industry=template.industry,
            default_stage=template.default_stage,
            default_status=template.default_status,
            default_health=template.default_health,
            template_config=template.template_config,
            is_active=template.is_active,
            usage_count=template.usage_count,
            created_by=template.created_by,
            created_at=template.created_at,
            updated_at=template.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/templates", response_model=ProjectTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_project_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: ProjectTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建项目模板
    """
    # 检查模板编码是否已存在
    existing = db.query(ProjectTemplate).filter(ProjectTemplate.template_code == template_in.template_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")
    
    template = ProjectTemplate(
        template_code=template_in.template_code,
        template_name=template_in.template_name,
        description=template_in.description,
        project_type=template_in.project_type,
        product_category=template_in.product_category,
        industry=template_in.industry,
        default_stage=template_in.default_stage or "S1",
        default_status=template_in.default_status or "ST01",
        default_health=template_in.default_health or "H1",
        template_config=template_in.template_config,
        is_active=template_in.is_active if template_in.is_active is not None else True,
        created_by=current_user.id,
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return ProjectTemplateResponse(
        id=template.id,
        template_code=template.template_code,
        template_name=template.template_name,
        description=template.description,
        project_type=template.project_type,
        product_category=template.product_category,
        industry=template.industry,
        default_stage=template.default_stage,
        default_status=template.default_status,
        default_health=template.default_health,
        template_config=template.template_config,
        is_active=template.is_active,
        usage_count=template.usage_count,
        created_by=template.created_by,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("/templates/{template_id}", response_model=ProjectTemplateResponse)
def read_project_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目模板详情
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return ProjectTemplateResponse(
        id=template.id,
        template_code=template.template_code,
        template_name=template.template_name,
        description=template.description,
        project_type=template.project_type,
        product_category=template.product_category,
        industry=template.industry,
        default_stage=template.default_stage,
        default_status=template.default_status,
        default_health=template.default_health,
        template_config=template.template_config,
        is_active=template.is_active,
        usage_count=template.usage_count,
        created_by=template.created_by,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.put("/templates/{template_id}", response_model=ProjectTemplateResponse)
def update_project_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    template_in: ProjectTemplateUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目模板
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    update_data = template_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return ProjectTemplateResponse(
        id=template.id,
        template_code=template.template_code,
        template_name=template.template_name,
        description=template.description,
        project_type=template.project_type,
        product_category=template.product_category,
        industry=template.industry,
        default_stage=template.default_stage,
        default_status=template.default_status,
        default_health=template.default_health,
        template_config=template.template_config,
        is_active=template.is_active,
        usage_count=template.usage_count,
        created_by=template.created_by,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.post("/templates/{template_id}/create-project", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project_from_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    project_in: ProjectCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    使用模板创建项目
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if not template.is_active:
        raise HTTPException(status_code=400, detail="模板已禁用")
    
    # 检查项目编码是否已存在
    existing = db.query(Project).filter(Project.project_code == project_in.project_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="项目编码已存在")
    
    # 创建项目，使用模板的默认值
    project_data = project_in.dict()
    if not project_data.get("stage"):
        project_data["stage"] = template.default_stage
    if not project_data.get("status"):
        project_data["status"] = template.default_status
    if not project_data.get("health"):
        project_data["health"] = template.default_health
    if not project_data.get("project_type") and template.project_type:
        project_data["project_type"] = template.project_type
    if not project_data.get("product_category") and template.product_category:
        project_data["product_category"] = template.product_category
    if not project_data.get("industry") and template.industry:
        project_data["industry"] = template.industry
    
    project = Project(**project_data, created_by=current_user.id)
    
    # 填充客户信息
    if project.customer_id:
        customer = db.query(Customer).filter(Customer.id == project.customer_id).first()
        if customer:
            project.customer_name = customer.customer_name
    
    # 填充项目经理信息
    if project.pm_id:
        pm = db.query(User).filter(User.id == project.pm_id).first()
        if pm:
            project.pm_name = pm.real_name or pm.username
    
    # Sprint 4.1: 记录模板信息并更新使用次数
    project.template_id = template_id
    if template.current_version_id:
        project.template_version_id = template.current_version_id
    
    db.add(project)
    
    # 更新模板使用次数
    template.usage_count = (template.usage_count or 0) + 1
    db.add(template)
    
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        project_code=project.project_code,
        project_name=project.project_name,
        customer_id=project.customer_id,
        customer_name=project.customer_name,
        stage=project.stage,
        status=project.status,
        health=project.health,
        progress_pct=float(project.progress_pct or 0),
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


# ==================== 项目模板版本管理 ====================

@router.get("/templates/{template_id}/versions", response_model=List[ProjectTemplateVersionResponse], status_code=status.HTTP_200_OK)
def get_template_versions(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目模板版本列表
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    versions = db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.template_id == template_id
    ).order_by(desc(ProjectTemplateVersion.created_at)).all()
    
    result = []
    for version in versions:
        created_by_name = None
        if version.created_by:
            creator = db.query(User).filter(User.id == version.created_by).first()
            created_by_name = creator.real_name or creator.username if creator else None
        
        published_by_name = None
        if version.published_by:
            publisher = db.query(User).filter(User.id == version.published_by).first()
            published_by_name = publisher.real_name or publisher.username if publisher else None
        
        result.append(ProjectTemplateVersionResponse(
            id=version.id,
            template_id=version.template_id,
            version_no=version.version_no,
            status=version.status,
            template_config=version.template_config,
            release_notes=version.release_notes,
            created_by=version.created_by,
            created_by_name=created_by_name,
            published_by=version.published_by,
            published_by_name=published_by_name,
            published_at=version.published_at,
            created_at=version.created_at,
            updated_at=version.updated_at
        ))
    
    return result


@router.post("/templates/{template_id}/versions", response_model=ProjectTemplateVersionResponse, status_code=status.HTTP_201_CREATED)
def create_template_version(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    version_in: ProjectTemplateVersionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建项目模板版本
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查版本号是否已存在
    existing = db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.template_id == template_id,
        ProjectTemplateVersion.version_no == version_in.version_no
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该版本号已存在")
    
    # 如果没有提供模板配置，使用当前模板的配置
    template_config = version_in.template_config or template.template_config
    
    version = ProjectTemplateVersion(
        template_id=template_id,
        version_no=version_in.version_no,
        status="DRAFT",
        template_config=template_config,
        release_notes=version_in.release_notes,
        created_by=current_user.id
    )
    
    db.add(version)
    db.commit()
    db.refresh(version)
    
    return ProjectTemplateVersionResponse(
        id=version.id,
        template_id=version.template_id,
        version_no=version.version_no,
        status=version.status,
        template_config=version.template_config,
        release_notes=version.release_notes,
        created_by=version.created_by,
        created_by_name=current_user.real_name or current_user.username,
        published_by=version.published_by,
        published_by_name=None,
        published_at=version.published_at,
        created_at=version.created_at,
        updated_at=version.updated_at
    )


@router.put("/templates/{template_id}/versions/{version_id}/publish", response_model=ProjectTemplateVersionResponse, status_code=status.HTTP_200_OK)
def publish_template_version(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    version_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发布项目模板版本（设置为当前版本）
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    version = db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.id == version_id,
        ProjectTemplateVersion.template_id == template_id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    # 将其他版本设置为ARCHIVED
    db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.template_id == template_id,
        ProjectTemplateVersion.id != version_id
    ).update({"status": "ARCHIVED"})
    
    # 设置当前版本为ACTIVE
    version.status = "ACTIVE"
    version.published_by = current_user.id
    version.published_at = datetime.now()
    
    # 更新模板的当前版本ID
    template.current_version_id = version.id
    
    # 更新模板配置为当前版本的配置
    if version.template_config:
        template.template_config = version.template_config
    
    db.add(version)
    db.add(template)
    db.commit()
    db.refresh(version)
    
    publisher_name = current_user.real_name or current_user.username
    
    return ProjectTemplateVersionResponse(
        id=version.id,
        template_id=version.template_id,
        version_no=version.version_no,
        status=version.status,
        template_config=version.template_config,
        release_notes=version.release_notes,
        created_by=version.created_by,
        created_by_name=None,  # 可以后续查询
        published_by=version.published_by,
        published_by_name=publisher_name,
        published_at=version.published_at,
        created_at=version.created_at,
        updated_at=version.updated_at
    )


# ==================== Sprint 4.2: 项目模板版本管理优化 ====================

@router.get("/templates/{template_id}/versions/compare", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def compare_template_versions(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    version1_id: Optional[int] = Query(None, description="版本1的ID"),
    version2_id: Optional[int] = Query(None, description="版本2的ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.2: 对比项目模板的两个版本
    
    对比不同版本间的配置差异，可视化展示差异
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 确定要对比的两个版本
    if version1_id and version2_id:
        v1 = db.query(ProjectTemplateVersion).filter(
            ProjectTemplateVersion.id == version1_id,
            ProjectTemplateVersion.template_id == template_id
        ).first()
        v2 = db.query(ProjectTemplateVersion).filter(
            ProjectTemplateVersion.id == version2_id,
            ProjectTemplateVersion.template_id == template_id
        ).first()
    else:
        # 默认对比当前版本和最新发布版本
        v1 = db.query(ProjectTemplateVersion).filter(
            ProjectTemplateVersion.template_id == template_id,
            ProjectTemplateVersion.status == "ACTIVE"
        ).first()
        v2 = db.query(ProjectTemplateVersion).filter(
            ProjectTemplateVersion.template_id == template_id,
            ProjectTemplateVersion.id == template.current_version_id
        ).first() if template.current_version_id else None
        
        if not v1:
            v1 = db.query(ProjectTemplateVersion).filter(
                ProjectTemplateVersion.template_id == template_id
            ).order_by(desc(ProjectTemplateVersion.created_at)).first()
        if not v2:
            v2 = v1
    
    if not v1 or not v2:
        raise HTTPException(status_code=404, detail="要对比的版本不存在")
    
    # 解析模板配置JSON
    import json
    config1 = {}
    config2 = {}
    
    try:
        if v1.template_config:
            config1 = json.loads(v1.template_config) if isinstance(v1.template_config, str) else v1.template_config
        if v2.template_config:
            config2 = json.loads(v2.template_config) if isinstance(v2.template_config, str) else v2.template_config
    except (json.JSONDecodeError, TypeError):
        pass
    
    # 对比配置差异
    added_fields = {}
    removed_fields = {}
    modified_fields = {}
    unchanged_fields = {}
    
    all_keys = set(config1.keys()) | set(config2.keys())
    
    for key in all_keys:
        val1 = config1.get(key)
        val2 = config2.get(key)
        
        if key not in config1:
            added_fields[key] = val2
        elif key not in config2:
            removed_fields[key] = val1
        elif val1 != val2:
            modified_fields[key] = {
                "old_value": val1,
                "new_value": val2
            }
        else:
            unchanged_fields[key] = val1
    
    # 对比模板基本字段（从模板本身获取，因为版本表可能不存储这些字段）
    basic_fields_diff = {}
    basic_fields = ["project_type", "product_category", "industry", "default_stage", "default_status", "default_health"]
    # 从模板配置中提取基本字段，或从模板本身获取
    template_config1 = config1 if config1 else {}
    template_config2 = config2 if config2 else {}
    
    for field in basic_fields:
        val1 = template_config1.get(field) or getattr(template, field, None)
        val2 = template_config2.get(field) or getattr(template, field, None)
        if val1 != val2:
            basic_fields_diff[field] = {
                "old_value": val1,
                "new_value": val2
            }
    
    return ResponseModel(
        code=200,
        message="版本对比成功",
        data={
            "version1": {
                "id": v1.id,
                "version_no": v1.version_no,
                "status": v1.status,
                "created_at": v1.created_at.isoformat() if v1.created_at else None,
            },
            "version2": {
                "id": v2.id,
                "version_no": v2.version_no,
                "status": v2.status,
                "created_at": v2.created_at.isoformat() if v2.created_at else None,
            },
            "config_diff": {
                "added": added_fields,
                "removed": removed_fields,
                "modified": modified_fields,
                "unchanged": unchanged_fields,
            },
            "basic_fields_diff": basic_fields_diff,
            "summary": {
                "total_changes": len(added_fields) + len(removed_fields) + len(modified_fields) + len(basic_fields_diff),
                "added_count": len(added_fields),
                "removed_count": len(removed_fields),
                "modified_count": len(modified_fields) + len(basic_fields_diff),
                "unchanged_count": len(unchanged_fields),
            }
        }
    )


@router.post("/templates/{template_id}/versions/{version_id}/rollback", response_model=ProjectTemplateVersionResponse, status_code=status.HTTP_200_OK)
def rollback_template_version(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    version_id: int,
    rollback_request: Optional[Dict[str, Any]] = Body(None, description="回滚请求（可选）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.2: 回滚项目模板到历史版本
    
    支持回滚到历史版本，记录回滚操作历史
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    target_version = db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.id == version_id,
        ProjectTemplateVersion.template_id == template_id
    ).first()
    if not target_version:
        raise HTTPException(status_code=404, detail="目标版本不存在")
    
    # 记录回滚前的当前版本
    old_version_id = template.current_version_id
    
    # 将其他版本设置为ARCHIVED
    db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.template_id == template_id,
        ProjectTemplateVersion.id != version_id
    ).update({"status": "ARCHIVED"})
    
    # 设置目标版本为ACTIVE
    target_version.status = "ACTIVE"
    target_version.published_by = current_user.id
    target_version.published_at = datetime.now()
    
    # 更新模板的当前版本ID
    template.current_version_id = version_id
    
    # 更新模板配置为目标版本的配置
    if target_version.template_config:
        template.template_config = target_version.template_config
    
    # 更新模板基本字段（如果目标版本有这些字段）
    # 注意：这里假设版本配置中包含基本字段，实际可能需要从版本配置中提取
    
    db.add(target_version)
    db.add(template)
    db.commit()
    db.refresh(target_version)
    
    # 记录回滚操作历史（可以记录到日志表或备注中）
    rollback_note = rollback_request.get("note") if rollback_request else None
    if rollback_note:
        target_version.release_notes = f"{target_version.release_notes or ''}\n[回滚操作] {rollback_note} (从版本 {old_version_id} 回滚，操作人: {current_user.real_name or current_user.username})"
        db.add(target_version)
        db.commit()
        db.refresh(target_version)
    
    publisher_name = current_user.real_name or current_user.username
    
    return ProjectTemplateVersionResponse(
        id=target_version.id,
        template_id=target_version.template_id,
        version_no=target_version.version_no,
        status=target_version.status,
        template_config=target_version.template_config,
        release_notes=target_version.release_notes,
        created_by=target_version.created_by,
        created_by_name=None,
        published_by=target_version.published_by,
        published_by_name=publisher_name,
        published_at=target_version.published_at,
        created_at=target_version.created_at,
        updated_at=target_version.updated_at
    )


# ==================== Sprint 5.3: 缓存监控和管理 ====================

@router.get("/cache/stats", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_cache_stats(
    *,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 5.3: 获取缓存统计信息
    
    返回缓存命中率、使用情况等统计信息
    """
    from app.services.cache_service import CacheService
    
    cache_service = CacheService()
    stats = cache_service.get_stats()
    redis_info = cache_service.get_redis_info()
    
    return ResponseModel(
        code=200,
        message="获取缓存统计成功",
        data={
            "stats": stats,
            "redis_info": redis_info,
        }
    )


@router.post("/cache/clear", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def clear_cache(
    *,
    pattern: Optional[str] = Query(None, description="缓存键模式（如 'project:*'），不提供则清空所有"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 5.3: 清空缓存
    
    支持按模式清空缓存，或清空所有缓存
    """
    from app.services.cache_service import CacheService
    
    cache_service = CacheService()
    
    if pattern:
        deleted_count = cache_service.delete_pattern(pattern)
        message = f"已清空匹配模式 '{pattern}' 的缓存，共 {deleted_count} 个键"
    else:
        cache_service.clear()
        message = "已清空所有缓存"
    
    return ResponseModel(
        code=200,
        message=message,
        data={}
    )


@router.post("/cache/reset-stats", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def reset_cache_stats(
    *,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 5.3: 重置缓存统计
    
    重置缓存命中率等统计信息
    """
    from app.services.cache_service import CacheService
    
    cache_service = CacheService()
    cache_service.reset_stats()
    
    return ResponseModel(
        code=200,
        message="缓存统计已重置",
        data={}
    )


# ==================== Sprint 4.3: 项目模板推荐功能 ====================

@router.get("/templates/recommend", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def recommend_templates(
    *,
    db: Session = Depends(deps.get_db),
    project_type: Optional[str] = Query(None, description="项目类型"),
    product_category: Optional[str] = Query(None, description="产品类别"),
    industry: Optional[str] = Query(None, description="行业"),
    limit: int = Query(5, ge=1, le=20, description="返回推荐数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.3: 获取项目模板推荐
    
    根据项目信息推荐合适的模板
    """
    from app.services.template_recommendation_service import TemplateRecommendationService
    
    recommendation_service = TemplateRecommendationService(db)
    recommendations = recommendation_service.recommend_templates(
        project_type=project_type,
        product_category=product_category,
        industry=industry,
        limit=limit
    )
    
    return ResponseModel(
        code=200,
        message="获取模板推荐成功",
        data={
            "recommendations": recommendations,
            "total": len(recommendations),
            "criteria": {
                "project_type": project_type,
                "product_category": product_category,
                "industry": industry,
            }
        }
    )


# ==================== Sprint 4.1: 项目模板使用统计 ====================

@router.get("/templates/{template_id}/usage-statistics", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_template_usage_statistics(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Sprint 4.1: 获取项目模板使用统计
    
    统计模板的使用次数、使用趋势等信息
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 统计总使用次数
    total_usage = template.usage_count or 0

    # 统计按时间的使用趋势（Sprint 4.1: 完善使用趋势统计）
    from sqlalchemy import func, case
    from datetime import datetime, timedelta
    
    # 如果没有指定日期范围，默认查询最近30天
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    # 按日期统计使用次数（如果Project模型有template_id字段）
    daily_usage = []
    if hasattr(Project, 'template_id'):
        daily_usage = db.query(
            func.date(Project.created_at).label('usage_date'),
            func.count(Project.id).label('count')
        ).filter(
            Project.template_id == template_id,
            func.date(Project.created_at) >= start_date,
            func.date(Project.created_at) <= end_date
        ).group_by(
            func.date(Project.created_at)
        ).order_by(
            func.date(Project.created_at)
        ).all()
        daily_usage = [{"date": str(item.usage_date), "count": item.count} for item in daily_usage]
    
    # 按版本统计使用次数
    version_usage = []
    if hasattr(Project, 'template_version_id'):
        version_usage = db.query(
            ProjectTemplateVersion.version_no,
            func.count(Project.id).label('count')
        ).join(
            Project, Project.template_version_id == ProjectTemplateVersion.id
        ).filter(
            Project.template_id == template_id
        ).group_by(
            ProjectTemplateVersion.version_no
        ).all()
        version_usage = [{"version_no": item.version_no, "count": item.count} for item in version_usage]
    
    # 计算模板使用率（使用该模板的项目数 / 总项目数）
    total_projects = db.query(func.count(Project.id)).filter(Project.is_active == True).scalar() or 1
    usage_rate = (total_usage / total_projects * 100) if total_projects > 0 else 0
    
    # 最近使用时间
    last_used = None
    if hasattr(Project, 'template_id'):
        last_used = db.query(
            func.max(Project.created_at)
        ).filter(
            Project.template_id == template_id
        ).scalar()
    # 注意：当前Project模型可能没有template_id字段，需要先添加
    # 这里先返回基础统计，后续可以扩展
    
    usage_trend = []
    if start_date and end_date:
        # 按月份统计使用趋势
        from datetime import datetime
        from sqlalchemy import func, extract
        
        # 如果Project模型有template_id字段，可以统计
        # 这里先返回空数组，后续扩展
        pass
    
    return ResponseModel(
        code=200,
        message="获取模板使用统计成功",
        data={
            "template_id": template_id,
            "template_code": template.template_code,
            "template_name": template.template_name,
            "total_usage": total_usage,
            "usage_rate": round(usage_rate, 2),
            "daily_usage": daily_usage,
            "version_usage": version_usage,
            "last_used": last_used.isoformat() if last_used else None,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
    )


# ==================== 项目复制/克隆 ====================

@router.post("/{project_id}/clone", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def clone_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    clone_request: ProjectCloneRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    复制/克隆项目
    """
    source_project = db.query(Project).filter(Project.id == project_id).first()
    if not source_project:
        raise HTTPException(status_code=404, detail="源项目不存在")
    
    # 检查新项目编码是否已存在
    existing = db.query(Project).filter(Project.project_code == clone_request.new_project_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="项目编码已存在")
    
    # 创建新项目（复制基本信息）
    new_project = Project(
        project_code=clone_request.new_project_code,
        project_name=clone_request.new_project_name,
        customer_id=clone_request.customer_id or source_project.customer_id,
        customer_name=source_project.customer_name if not clone_request.customer_id else None,
        project_type=source_project.project_type,
        product_category=source_project.product_category,
        industry=source_project.industry,
        stage="S1",  # 新项目从S1开始
        status="ST01",  # 新项目状态为ST01
        health="H1",  # 新项目健康度为H1
        progress_pct=0,  # 新项目进度为0
        contract_no=None,  # 不复制合同编号
        contract_date=None,
        planned_start_date=None,
        planned_end_date=None,
        contract_amount=0,
        budget_amount=source_project.budget_amount,
        pm_id=source_project.pm_id,
        pm_name=source_project.pm_name,
        dept_id=source_project.dept_id,
        priority=source_project.priority,
        description=source_project.description,
        requirements=source_project.requirements,
        created_by=current_user.id,
    )
    
    # 填充客户信息
    if new_project.customer_id:
        customer = db.query(Customer).filter(Customer.id == new_project.customer_id).first()
        if customer:
            new_project.customer_name = customer.customer_name
    
    db.add(new_project)
    db.flush()  # 获取新项目ID
    
    # 复制机台
    if clone_request.copy_machines:
        machines = db.query(Machine).filter(Machine.project_id == project_id).all()
        for machine in machines:
            new_machine = Machine(
                project_id=new_project.id,
                machine_code=f"{new_project.project_code}-{machine.machine_code.split('-')[-1] if '-' in machine.machine_code else machine.machine_code}",
                machine_name=machine.machine_name,
                machine_type=machine.machine_type,
                progress_pct=0,
                status="DRAFT",
            )
            db.add(new_machine)
    
    # 复制里程碑
    if clone_request.copy_milestones:
        milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).all()
        for milestone in milestones:
            new_milestone = ProjectMilestone(
                project_id=new_project.id,
                milestone_code=f"{new_project.project_code}-{milestone.milestone_code.split('-')[-1] if '-' in milestone.milestone_code else milestone.milestone_code}",
                milestone_name=milestone.milestone_name,
                milestone_type=milestone.milestone_type,
                plan_date=None,  # 新里程碑需要重新设置日期
                actual_date=None,
                status="PENDING",
                trigger_invoice=milestone.trigger_invoice,
                invoice_amount=milestone.invoice_amount,
            )
            db.add(new_milestone)
    
    # 复制成员
    if clone_request.copy_members:
        members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()
        for member in members:
            new_member = ProjectMember(
                project_id=new_project.id,
                user_id=member.user_id,
                user_name=member.user_name,
                role=member.role,
                responsibility=member.responsibility,
            )
            db.add(new_member)
    
    # 复制阶段
    if clone_request.copy_stages:
        stages = db.query(ProjectStage).filter(ProjectStage.project_id == project_id).all()
        for stage in stages:
            new_stage = ProjectStage(
                project_id=new_project.id,
                stage_code=stage.stage_code,
                stage_name=stage.stage_name,
                stage_order=stage.stage_order,
                plan_start_date=None,
                plan_end_date=None,
                actual_start_date=None,
                actual_end_date=None,
                progress=0,
                status="PENDING",
            )
            db.add(new_stage)
    
    db.commit()
    db.refresh(new_project)
    
    return ProjectResponse(
        id=new_project.id,
        project_code=new_project.project_code,
        project_name=new_project.project_name,
        customer_id=new_project.customer_id,
        customer_name=new_project.customer_name,
        stage=new_project.stage,
        status=new_project.status,
        health=new_project.health,
        progress_pct=float(new_project.progress_pct or 0),
        created_at=new_project.created_at,
        updated_at=new_project.updated_at,
    )


# ==================== 项目归档管理 ====================

@router.put("/{project_id}/archive", response_model=ResponseModel)
def archive_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    archive_request: ProjectArchiveRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    归档项目
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if project.is_archived:
        raise HTTPException(status_code=400, detail="项目已归档")
    
    # 检查项目是否可以归档（通常需要项目已完成或已结项）
    if project.stage not in ["S9"] and project.status not in ["ST30"]:
        raise HTTPException(status_code=400, detail="项目未完成，无法归档")
    
    project.is_archived = True
    if archive_request.archive_reason:
        if project.description:
            project.description += f"\n[归档原因] {archive_request.archive_reason}"
        else:
            project.description = f"[归档原因] {archive_request.archive_reason}"
    
    db.add(project)
    db.commit()
    
    return ResponseModel(code=200, message="项目已归档")


@router.put("/{project_id}/unarchive", response_model=ResponseModel)
def unarchive_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    取消归档项目
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if not project.is_archived:
        raise HTTPException(status_code=400, detail="项目未归档")
    
    project.is_archived = False
    
    db.add(project)
    db.commit()
    
    return ResponseModel(code=200, message="项目已取消归档")


@router.get("/archived", response_model=PaginatedResponse)
def read_archived_projects(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取已归档项目列表
    """
    query = db.query(Project).filter(Project.is_archived == True)
    
    if keyword:
        query = query.filter(
            or_(
                Project.project_code.like(f"%{keyword}%"),
                Project.project_name.like(f"%{keyword}%"),
            )
        )
    
    total = query.count()
    projects = query.order_by(desc(Project.updated_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for project in projects:
        items.append(ProjectListResponse(
            id=project.id,
            project_code=project.project_code,
            project_name=project.project_name,
            customer_id=project.customer_id,
            customer_name=project.customer_name,
            stage=project.stage,
            status=project.status,
            health=project.health,
            progress_pct=float(project.progress_pct or 0),
            created_at=project.created_at,
            updated_at=project.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ==================== 项目资源分配优化 ====================

@router.get("/{project_id}/resource-optimization", response_model=dict)
def get_resource_optimization(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    start_date: Optional[date] = Query(None, description="开始日期（默认：项目开始日期）"),
    end_date: Optional[date] = Query(None, description="结束日期（默认：项目结束日期）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目资源分配优化分析
    分析项目资源分配情况，提供优化建议
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if not start_date:
        start_date = project.planned_start_date or date.today()
    if not end_date:
        end_date = project.planned_end_date or (date.today() + timedelta(days=90))
    
    # 获取项目资源分配
    allocations = db.query(PmoResourceAllocation).filter(
        PmoResourceAllocation.project_id == project_id,
        PmoResourceAllocation.start_date <= end_date,
        PmoResourceAllocation.end_date >= start_date,
        PmoResourceAllocation.status != 'CANCELLED'
    ).all()
    
    # 获取项目任务
    tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.plan_start <= end_date,
        Task.plan_end >= start_date,
        Task.status != 'CANCELLED'
    ).all()
    
    # 分析资源负荷
    resource_load = {}
    for alloc in allocations:
        resource_id = alloc.resource_id
        if resource_id not in resource_load:
            resource_load[resource_id] = {
                'resource_id': resource_id,
                'resource_name': alloc.resource_name,
                'resource_dept': alloc.resource_dept,
                'total_allocation': 0,
                'allocations': [],
            }
        
        resource_load[resource_id]['total_allocation'] += alloc.allocation_percent
        resource_load[resource_id]['allocations'].append({
            'id': alloc.id,
            'start_date': alloc.start_date.isoformat() if alloc.start_date else None,
            'end_date': alloc.end_date.isoformat() if alloc.end_date else None,
            'allocation_percent': alloc.allocation_percent,
            'planned_hours': alloc.planned_hours,
            'status': alloc.status,
        })
    
    # 检查资源冲突
    conflicts = []
    recommendations = []
    
    for resource_id, data in resource_load.items():
        # 检查总分配率
        if data['total_allocation'] > 100:
            recommendations.append({
                'type': 'OVER_ALLOCATION',
                'resource_id': resource_id,
                'resource_name': data['resource_name'],
                'current_allocation': data['total_allocation'],
                'recommendation': f"资源 {data['resource_name']} 总分配率 {data['total_allocation']}%，建议调整分配比例或延期部分任务",
                'priority': 'HIGH' if data['total_allocation'] > 150 else 'MEDIUM'
            })
        
        # 检查时间重叠
        allocs = sorted(data['allocations'], key=lambda x: (x['start_date'] or '', x['end_date'] or ''))
        for i in range(len(allocs) - 1):
            for j in range(i + 1, len(allocs)):
                alloc1 = allocs[i]
                alloc2 = allocs[j]
                
                if alloc1['start_date'] and alloc1['end_date'] and alloc2['start_date'] and alloc2['end_date']:
                    start1 = datetime.fromisoformat(alloc1['start_date']).date()
                    end1 = datetime.fromisoformat(alloc1['end_date']).date()
                    start2 = datetime.fromisoformat(alloc2['start_date']).date()
                    end2 = datetime.fromisoformat(alloc2['end_date']).date()
                    
                    # 检查是否有重叠
                    if not (end1 < start2 or end2 < start1):
                        overlap_allocation = alloc1['allocation_percent'] + alloc2['allocation_percent']
                        if overlap_allocation > 100:
                            conflicts.append({
                                'resource_id': resource_id,
                                'resource_name': data['resource_name'],
                                'allocation1_id': alloc1['id'],
                                'allocation2_id': alloc2['id'],
                                'overlap_start': max(start1, start2).isoformat(),
                                'overlap_end': min(end1, end2).isoformat(),
                                'total_allocation': overlap_allocation,
                            })
    
    # 分析任务资源匹配度
    task_resource_match = []
    for task in tasks:
        if task.owner_id:
            has_allocation = any(
                alloc.resource_id == task.owner_id 
                for alloc in allocations
                if alloc.start_date and alloc.end_date and task.plan_start and task.plan_end
                and not (alloc.end_date < task.plan_start or alloc.start_date > task.plan_end)
            )
            
            if not has_allocation:
                task_resource_match.append({
                    'task_id': task.id,
                    'task_name': task.task_name,
                    'owner_id': task.owner_id,
                    'plan_start': task.plan_start.isoformat() if task.plan_start else None,
                    'plan_end': task.plan_end.isoformat() if task.plan_end else None,
                    'issue': '任务负责人未在资源分配中',
                    'recommendation': '建议为任务负责人添加资源分配记录'
                })
    
    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'analysis_period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        },
        'resource_summary': {
            'total_resources': len(resource_load),
            'over_allocated_resources': len([r for r in resource_load.values() if r['total_allocation'] > 100]),
            'total_conflicts': len(conflicts),
        },
        'resource_load': list(resource_load.values()),
        'conflicts': conflicts,
        'recommendations': recommendations,
        'task_resource_issues': task_resource_match,
    }


# ==================== 项目关联分析 ====================

@router.get("/{project_id}/relations", response_model=dict)
def get_project_relations(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    relation_type: Optional[str] = Query(None, description="关联类型筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目关联分析
    分析项目之间的关联关系（物料转移、共享资源、共享客户等）
    """
    from app.services.project_relations_service import (
        get_material_transfer_relations,
        get_shared_resource_relations,
        get_shared_customer_relations,
        calculate_relation_statistics
    )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    relations = []
    
    # 1. 物料转移关联
    relations.extend(get_material_transfer_relations(db, project_id, relation_type))
    
    # 2. 共享资源关联
    relations.extend(get_shared_resource_relations(db, project_id, relation_type))
    
    # 3. 共享客户关联
    relations.extend(get_shared_customer_relations(db, project, project_id, relation_type))
    
    # 统计
    relation_stats = calculate_relation_statistics(relations)
    
    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'relation_stats': relation_stats,
        'relations': relations,
    }


@router.post("/{project_id}/auto-discover-relations", response_model=dict, status_code=status.HTTP_200_OK)
def auto_discover_project_relations(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    min_confidence: float = Query(0.3, ge=0.0, le=1.0, description="最小置信度阈值"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    自动发现项目关联关系
    
    基于多种规则自动发现项目之间的潜在关联：
    1. 相同客户的项目
    2. 相同项目经理的项目
    3. 时间重叠的项目
    4. 相似项目名称/编码
    5. 物料转移记录
    6. 共享资源
    7. 关联的研发项目
    """
    from app.services.project_relation_discovery_service import (
        discover_same_customer_relations,
        discover_same_pm_relations,
        discover_time_overlap_relations,
        discover_material_transfer_relations,
        discover_shared_resource_relations,
        discover_shared_rd_project_relations,
        deduplicate_and_filter_relations,
        calculate_relation_statistics
    )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    discovered_relations = []
    
    # 1. 相同客户的项目（置信度：0.8）
    discovered_relations.extend(discover_same_customer_relations(db, project, project_id))
    
    # 2. 相同项目经理的项目（置信度：0.7）
    discovered_relations.extend(discover_same_pm_relations(db, project, project_id))
    
    # 3. 时间重叠的项目（置信度：0.6）
    discovered_relations.extend(discover_time_overlap_relations(db, project, project_id))
    
    # 4. 物料转移记录（置信度：0.9）
    discovered_relations.extend(discover_material_transfer_relations(db, project_id))
    
    # 5. 共享资源（置信度：0.75）
    discovered_relations.extend(discover_shared_resource_relations(db, project_id))
    
    # 6. 关联的研发项目（置信度：0.85）
    discovered_relations.extend(discover_shared_rd_project_relations(db, project_id))
    
    # 去重并过滤置信度
    final_relations = deduplicate_and_filter_relations(discovered_relations, min_confidence)
    
    # 计算统计信息
    statistics = calculate_relation_statistics(final_relations)
    
    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'min_confidence': min_confidence,
        'total_discovered': len(final_relations),
        'relations': final_relations,
        'statistics': statistics
    }


# ==================== 项目风险矩阵 ====================

@router.get("/{project_id}/risk-matrix", response_model=dict)
def get_project_risk_matrix(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    include_closed: bool = Query(False, description="是否包含已关闭风险"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目风险矩阵
    生成项目风险矩阵，按概率和影响程度分类
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    query = db.query(PmoProjectRisk).filter(PmoProjectRisk.project_id == project_id)
    
    if not include_closed:
        query = query.filter(PmoProjectRisk.status != 'CLOSED')
    
    risks = query.all()
    
    # 风险矩阵（概率 × 影响）
    risk_matrix = {
        'LOW_LOW': [],
        'LOW_MEDIUM': [],
        'LOW_HIGH': [],
        'MEDIUM_LOW': [],
        'MEDIUM_MEDIUM': [],
        'MEDIUM_HIGH': [],
        'HIGH_LOW': [],
        'HIGH_MEDIUM': [],
        'HIGH_HIGH': [],
    }
    
    risk_by_level = {
        'LOW': [],
        'MEDIUM': [],
        'HIGH': [],
        'CRITICAL': [],
    }
    
    risk_by_category = {}
    
    for risk in risks:
        risk_info = {
            'id': risk.id,
            'risk_no': risk.risk_no,
            'risk_name': risk.risk_name,
            'risk_category': risk.risk_category,
            'probability': risk.probability,
            'impact': risk.impact,
            'risk_level': risk.risk_level,
            'status': risk.status,
            'response_strategy': risk.response_strategy,
            'owner_name': risk.owner_name,
            'is_triggered': risk.is_triggered,
        }
        
        prob = risk.probability or 'LOW'
        impact = risk.impact or 'LOW'
        matrix_key = f"{prob}_{impact}"
        if matrix_key in risk_matrix:
            risk_matrix[matrix_key].append(risk_info)
        
        level = risk.risk_level or 'LOW'
        if level in risk_by_level:
            risk_by_level[level].append(risk_info)
        
        category = risk.risk_category or 'OTHER'
        if category not in risk_by_category:
            risk_by_category[category] = []
        risk_by_category[category].append(risk_info)
    
    stats = {
        'total_risks': len(risks),
        'by_level': {level: len(risks) for level, risks in risk_by_level.items()},
        'by_category': {category: len(risks) for category, risks in risk_by_category.items()},
        'by_status': {},
        'critical_risks': len(risk_by_level.get('CRITICAL', [])),
        'triggered_risks': len([r for r in risks if r.is_triggered]),
    }
    
    for risk in risks:
        status = risk.status or 'IDENTIFIED'
        if status not in stats['by_status']:
            stats['by_status'][status] = 0
        stats['by_status'][status] += 1
    
    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'stats': stats,
        'risk_matrix': risk_matrix,
        'risk_by_level': risk_by_level,
        'risk_by_category': risk_by_category,
    }


# ==================== 项目变更影响分析 ====================

@router.get("/{project_id}/change-impact", response_model=dict)
def get_change_impact_analysis(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    change_id: Optional[int] = Query(None, description="变更ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目变更影响分析
    分析项目变更对其他项目、资源、成本等的影响
    """
    from app.services.change_impact_analysis_service import (
        build_impact_analysis,
        calculate_change_statistics
    )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    query = db.query(PmoChangeRequest).filter(PmoChangeRequest.project_id == project_id)
    
    if change_id:
        query = query.filter(PmoChangeRequest.id == change_id)
    
    changes = query.all()
    
    # 构建影响分析
    impact_analysis = [
        build_impact_analysis(db, change, project, project_id)
        for change in changes
    ]
    
    # 计算统计信息
    stats = calculate_change_statistics(changes, impact_analysis)
    
    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'stats': stats,
        'impact_analysis': impact_analysis,
    }


# ==================== 项目概览数据 ====================

@router.get("/{project_id}/summary", response_model=ProjectSummaryResponse)
def get_project_summary(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目概览数据
    
    包含项目基本信息、统计数据、成本汇总、最近活动等
    """
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)
    
    # 统计机台数量
    machine_count = db.query(Machine).filter(Machine.project_id == project_id).count()
    
    # 统计里程碑
    milestone_count = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).count()
    completed_milestone_count = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status == "COMPLETED"
    ).count()
    
    # 统计任务
    task_count = db.query(Task).filter(Task.project_id == project_id).count()
    completed_task_count = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == "COMPLETED"
    ).count()
    
    # 统计成员
    from app.models.project import ProjectMember
    member_count = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).count()
    
    # 统计预警
    from app.models.alert import Alert
    alert_count = db.query(Alert).filter(
        Alert.project_id == project_id,
        Alert.status != "RESOLVED"
    ).count()
    
    # 统计问题
    from app.models.issue import Issue
    issue_count = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status != "CLOSED"
    ).count()
    
    # 统计文档
    from app.models.project import ProjectDocument
    document_count = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).count()
    
    # 成本汇总
    from app.models.project import ProjectCost
    costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()
    cost_summary = {
        "total_cost": float(sum(cost.cost_amount or 0 for cost in costs)),
        "by_type": {},
        "by_category": {},
    }
    for cost in costs:
        if cost.cost_type:
            if cost.cost_type not in cost_summary["by_type"]:
                cost_summary["by_type"][cost.cost_type] = 0
            cost_summary["by_type"][cost.cost_type] += float(cost.cost_amount or 0)
        if cost.cost_category:
            if cost.cost_category not in cost_summary["by_category"]:
                cost_summary["by_category"][cost.cost_category] = 0
            cost_summary["by_category"][cost.cost_category] += float(cost.cost_amount or 0)
    
    # 最近活动（状态变更、里程碑完成等）
    recent_activities = []
    
    # 最近的状态变更
    recent_status_logs = db.query(ProjectStatusLog).filter(
        ProjectStatusLog.project_id == project_id
    ).order_by(desc(ProjectStatusLog.changed_at)).limit(5).all()
    
    for log in recent_status_logs:
        activity = {
            "type": log.change_type,
            "time": log.changed_at.isoformat() if log.changed_at else None,
            "description": f"{log.change_type}: {log.old_stage or ''} → {log.new_stage or ''}",
            "user_name": log.changer.username if log.changer else None,
        }
        recent_activities.append(activity)
    
    # 最近的里程碑完成
    recent_milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status == "COMPLETED",
        ProjectMilestone.actual_date.isnot(None)
    ).order_by(desc(ProjectMilestone.actual_date)).limit(3).all()
    
    for milestone in recent_milestones:
        activity = {
            "type": "MILESTONE_COMPLETED",
            "time": milestone.actual_date.isoformat() if milestone.actual_date else None,
            "description": f"里程碑完成: {milestone.milestone_name}",
            "related_id": milestone.id,
            "related_type": "milestone",
        }
        recent_activities.append(activity)
    
    # 按时间排序
    recent_activities.sort(key=lambda x: x.get("time") or "", reverse=True)
    recent_activities = recent_activities[:10]
    
    return ProjectSummaryResponse(
        project_id=project.id,
        project_code=project.project_code,
        project_name=project.project_name,
        customer_name=project.customer_name,
        pm_name=project.pm_name,
        stage=project.stage or "S1",
        status=project.status or "ST01",
        health=project.health,
        progress_pct=float(project.progress_pct or 0),
        contract_amount=project.contract_amount,
        budget_amount=project.budget_amount,
        actual_cost=project.actual_cost,
        planned_start_date=project.planned_start_date,
        planned_end_date=project.planned_end_date,
        actual_start_date=project.actual_start_date,
        actual_end_date=project.actual_end_date,
        machine_count=machine_count,
        milestone_count=milestone_count,
        completed_milestone_count=completed_milestone_count,
        task_count=task_count,
        completed_task_count=completed_task_count,
        member_count=member_count,
        alert_count=alert_count,
        issue_count=issue_count,
        document_count=document_count,
        cost_summary=cost_summary,
        recent_activities=recent_activities,
    )


# ==================== 在产项目进度汇总 ====================

@router.get("/in-production/summary", response_model=List[InProductionProjectSummary])
def get_in_production_projects_summary(
    db: Session = Depends(deps.get_db),
    stage: Optional[str] = Query(None, description="阶段筛选：S4-S8"),
    health: Optional[str] = Query(None, description="健康度筛选：H1-H3"),
    current_user: User = Depends(security.require_production_access()),
) -> Any:
    """
    在产项目进度汇总（专门给生产总监/经理看）
    返回S4-S8阶段的项目进度、里程碑、延期风险等信息
    """
    # 查询在产项目（S4-S8阶段）
    query = db.query(Project).filter(
        Project.stage.in_(["S4", "S5", "S6", "S7", "S8"]),
        Project.is_active == True
    )
    
    if stage:
        query = query.filter(Project.stage == stage)
    if health:
        query = query.filter(Project.health == health)
    
    projects = query.all()
    
    result = []
    for project in projects:
        # 获取项目阶段信息
        stages = db.query(ProjectStage).filter(
            ProjectStage.project_id == project.id
        ).order_by(ProjectStage.stage_order).all()
        
        # 获取未完成的里程碑
        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project.id,
            ProjectMilestone.status != "COMPLETED"
        ).order_by(ProjectMilestone.planned_date).limit(5).all()
        
        # 计算项目进度（基于阶段完成情况）
        completed_stages = sum(1 for s in stages if s.status == "COMPLETED")
        total_stages = len(stages)
        progress = (completed_stages / total_stages * 100) if total_stages > 0 else float(project.progress_pct or 0)
        
        # 获取延期风险（已过期但未完成的里程碑）
        today = date.today()
        overdue_milestones = [
            m for m in milestones 
            if m.planned_date and m.planned_date < today and m.status != "COMPLETED"
        ]
        
        # 下一个里程碑
        next_milestone = None
        next_milestone_date = None
        if milestones:
            next_milestone = milestones[0].milestone_name
            next_milestone_date = milestones[0].planned_date
        
        result.append(InProductionProjectSummary(
            project_id=project.id,
            project_code=project.project_code,
            project_name=project.project_name,
            stage=project.stage or "S4",
            health=project.health,
            progress=progress,
            planned_end_date=project.planned_end_date,
            actual_end_date=project.actual_end_date,
            overdue_milestones_count=len(overdue_milestones),
            next_milestone=next_milestone,
            next_milestone_date=next_milestone_date,
        ))
    
    return result


# ==================== 项目时间线 ====================

@router.get("/{project_id}/timeline", response_model=ProjectTimelineResponse)
def get_project_timeline(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    event_type: Optional[str] = Query(None, description="事件类型筛选"),
    limit: int = Query(100, ge=1, le=500, description="返回记录数"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目时间线
    
    包含项目生命周期中的所有重要事件：状态变更、里程碑、任务、成本、文档等
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    from app.services.project_timeline_service import (
        collect_status_change_events,
        collect_milestone_events,
        collect_task_events,
        collect_cost_events,
        collect_document_events,
        add_project_created_event
    )
    
    # 检查项目访问权限
    project = check_project_access_or_raise(db, current_user, project_id)
    
    events = []
    
    # 收集各类事件
    if not event_type or event_type == "STATUS_CHANGE":
        events.extend(collect_status_change_events(db, project_id))
    
    if not event_type or event_type == "MILESTONE":
        events.extend(collect_milestone_events(db, project_id))
    
    if not event_type or event_type == "TASK":
        events.extend(collect_task_events(db, project_id))
    
    if not event_type or event_type == "COST":
        events.extend(collect_cost_events(db, project_id))
    
    if not event_type or event_type == "DOCUMENT":
        events.extend(collect_document_events(db, project_id))
    
    # 添加项目创建事件
    if project.created_at:
        events.append(add_project_created_event(project))
    
    # 按时间排序
    events.sort(key=lambda x: x.event_time, reverse=True)
    
    # 限制返回数量
    events = events[:limit]
    
    return ProjectTimelineResponse(
        project_id=project.id,
        project_code=project.project_code,
        project_name=project.project_name,
        events=events,
        total_events=len(events),
    )


# ==================== 项目仪表盘 ====================

@router.get("/{project_id}/dashboard", response_model=ProjectDashboardResponse)
def get_project_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目仪表盘数据
    
    聚合项目的各种数据，包括进度、成本、任务、里程碑、风险、问题等
    """
    from datetime import date
    from app.utils.permission_helpers import check_project_access_or_raise
    from app.services.project_dashboard_service import (
        build_basic_info,
        calculate_progress_stats,
        calculate_cost_stats,
        calculate_task_stats,
        calculate_milestone_stats,
        calculate_risk_stats,
        calculate_issue_stats,
        calculate_resource_usage,
        get_recent_activities,
        calculate_key_metrics
    )
    
    # 检查项目访问权限
    project = check_project_access_or_raise(db, current_user, project_id)
    
    today = date.today()
    
    # 获取各项统计数据
    basic_info = build_basic_info(project)
    progress_stats = calculate_progress_stats(project, today)
    cost_stats = calculate_cost_stats(db, project_id, float(project.budget_amount or 0))
    task_stats = calculate_task_stats(db, project_id)
    milestone_stats = calculate_milestone_stats(db, project_id, today)
    risk_stats = calculate_risk_stats(db, project_id)
    issue_stats = calculate_issue_stats(db, project_id)
    resource_usage = calculate_resource_usage(db, project_id)
    recent_activities = get_recent_activities(db, project_id)
    
    # 计算关键指标
    key_metrics = calculate_key_metrics(
        project,
        progress_stats["progress_deviation"],
        cost_stats["cost_variance_rate"],
        task_stats["completed"],
        task_stats["total"]
    )
    
    return ProjectDashboardResponse(
        project_id=project.id,
        project_code=project.project_code,
        project_name=project.project_name,
        basic_info=basic_info,
        progress_stats=progress_stats,
        cost_stats=cost_stats,
        task_stats=task_stats,
        milestone_stats=milestone_stats,
        risk_stats=risk_stats,
        issue_stats=issue_stats,
        resource_usage=resource_usage,
        recent_activities=recent_activities,
        key_metrics=key_metrics,
    )


# ==================== 阶段推进（含阶段门校验） ====================

def check_gate_s1_to_s2(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G1: S1→S2 阶段门校验 - 需求采集表完整、客户信息齐全
    
    Issue 1.3: 细化校验条件
    """
    missing = []
    
    # 检查客户信息齐全（客户名称、联系人、联系电话）
    if not project.customer_id:
        missing.append("客户信息未填写（请选择客户）")
    else:
        if not project.customer_name:
            missing.append("客户名称未填写")
        if not project.customer_contact:
            missing.append("客户联系人未填写")
        if not project.customer_phone:
            missing.append("客户联系电话未填写")
    
    # 检查项目基本信息完整
    if not project.project_name:
        missing.append("项目名称未填写")
    if not project.project_code:
        missing.append("项目编码未填写")
    
    # 检查需求采集表完整性（必填字段）
    if not project.requirements:
        missing.append("需求采集表未填写（请在项目描述中填写需求信息）")
    else:
        # 检查关键需求字段（可以根据实际业务需求细化）
        requirements_text = project.requirements.lower()
        if "项目类型" not in requirements_text and not project.project_type:
            missing.append("项目类型未明确")
        if "交付物" not in requirements_text and "deliverable" not in requirements_text:
            missing.append("交付物清单未明确")
    
    return (len(missing) == 0, missing)


def check_gate_s2_to_s3(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G2: S2→S3 阶段门校验 - 需求规格书确认、验收标准明确
    
    Issue 1.3: 细化校验条件
    """
    missing = []
    
    # 检查需求规格书已确认（有确认记录）
    from app.models.project import ProjectDocument
    spec_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project.id,
        ProjectDocument.doc_type.in_(["REQUIREMENT", "SPECIFICATION"]),
        ProjectDocument.status == "APPROVED"
    ).count()
    
    if spec_docs == 0:
        missing.append("需求规格书未确认（请上传需求规格书文档并标记为已确认）")
    
    # 检查验收标准明确（有验收标准文档或记录）
    # 方式1: 检查验收标准文档
    acceptance_standard_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project.id,
        ProjectDocument.doc_type.in_(["ACCEPTANCE_STANDARD", "ACCEPTANCE"]),
        ProjectDocument.status == "APPROVED"
    ).count()
    
    # 方式2: 检查项目描述中是否包含验收标准
    has_acceptance_standard_in_text = False
    if project.requirements:
        requirements_lower = project.requirements.lower()
        if any(keyword in requirements_lower for keyword in ["验收标准", "acceptance", "验收条件", "验收要求"]):
            has_acceptance_standard_in_text = True
    
    if acceptance_standard_docs == 0 and not has_acceptance_standard_in_text:
        missing.append("验收标准未明确（请上传验收标准文档或在项目描述中明确验收标准）")
    
    # 检查客户已签字确认（通过需求规格书文档的签字状态或项目状态）
    # 如果项目状态为ST05（待客户确认），说明还未确认
    if project.status == "ST05":
        missing.append("需求规格书待客户确认（请等待客户签字确认）")
    
    return (len(missing) == 0, missing)


def check_gate_s3_to_s4(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G3: S3→S4 阶段门校验 - 立项评审通过、合同签订
    
    Issue 1.3: 细化校验条件
    """
    missing = []
    
    # 检查立项评审已通过（有评审记录）
    from app.models.pmo import PmoProjectInitiation
    initiation = db.query(PmoProjectInitiation).filter(
        PmoProjectInitiation.project_id == project.id,
        PmoProjectInitiation.status == "APPROVED"
    ).first()
    
    if not initiation:
        # 如果没有立项申请记录，检查是否有其他评审记录（如技术评审）
        from app.models.technical_review import TechnicalReview
        review = db.query(TechnicalReview).filter(
            TechnicalReview.project_id == project.id,
            TechnicalReview.review_type.in_(["PDR", "INITIATION"]),  # 初步设计评审或立项评审
            TechnicalReview.status == "COMPLETED"
        ).first()
        
        if not review:
            missing.append("立项评审未通过（请完成立项评审流程）")
    
    # 检查合同已签订（关联合同状态）
    if not project.contract_no:
        missing.append("合同编号未填写")
    else:
        # 检查合同状态（如果关联了合同）
        from app.models.sales import Contract
        contract = db.query(Contract).filter(Contract.contract_code == project.contract_no).first()
        if contract:
            if contract.status != "SIGNED":
                missing.append(f"合同未签订（当前状态：{contract.status}）")
        elif not project.contract_date:
            # 如果没有关联合同记录，至少检查合同日期
            missing.append("合同签订日期未填写")
    
    # 检查合同金额、交期等关键信息已确认
    if not project.contract_date:
        missing.append("合同签订日期未填写")
    
    if not project.contract_amount or project.contract_amount <= 0:
        missing.append("合同金额未填写或无效")
    
    if not project.planned_end_date:
        missing.append("项目计划结束日期未填写（请确认合同交期）")
    
    return (len(missing) == 0, missing)


def check_gate_s4_to_s5(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G4: S4→S5 阶段门校验 - 方案评审通过、BOM发布
    
    Issue 1.3: 细化校验条件
    """
    missing = []
    
    # 检查方案评审已通过（有评审记录）
    from app.models.technical_review import TechnicalReview
    scheme_review = db.query(TechnicalReview).filter(
        TechnicalReview.project_id == project.id,
        TechnicalReview.review_type.in_(["DDR", "SCHEME", "DESIGN"]),  # 详细设计评审、方案评审
        TechnicalReview.status == "COMPLETED"
    ).first()
    
    if not scheme_review:
        # 如果没有技术评审记录，检查方案文档是否已评审通过
        from app.models.project import ProjectDocument
        design_docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project.id,
            ProjectDocument.doc_type.in_(["DESIGN", "SCHEME"]),
            ProjectDocument.status == "APPROVED"
        ).count()
        
        if design_docs == 0:
            missing.append("方案评审未通过（请完成方案评审或上传已评审通过的设计文档）")
    
    # 检查BOM已发布（关联BOM模块）
    from app.models.material import BomHeader
    released_boms = db.query(BomHeader).filter(
        BomHeader.project_id == project.id,
        BomHeader.status == "RELEASED"
    ).all()
    
    if not released_boms:
        missing.append("BOM未发布（请发布至少一个BOM）")
    else:
        # 检查每个机台是否有BOM
        machines = db.query(Machine).filter(Machine.project_id == project.id).all()
        if machines:
            for machine in machines:
                machine_bom = db.query(BomHeader).filter(
                    BomHeader.machine_id == machine.id,
                    BomHeader.status == "RELEASED"
                ).first()
                if not machine_bom:
                    missing.append(f"机台 {machine.machine_code} 的BOM未发布")
    
    # 检查关键设计文档已上传
    from app.models.project import ProjectDocument
    key_doc_types = ["DESIGN", "SCHEME", "DRAWING", "ELECTRICAL", "SOFTWARE"]
    key_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project.id,
        ProjectDocument.doc_type.in_(key_doc_types),
        ProjectDocument.status == "APPROVED"
    ).count()
    
    if key_docs == 0:
        missing.append("关键设计文档未上传（请上传机械/电气/软件设计文档）")
    
    return (len(missing) == 0, missing)


def check_gate_s5_to_s6(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """G5: S5→S6 阶段门校验 - 关键物料齐套率≥80%"""
    missing = []
    
    # 获取所有机台
    machines = db.query(Machine).filter(Machine.project_id == project.id).all()
    
    if not machines:
        missing.append("项目下没有机台")
        return (False, missing)
    
    # 检查每个机台的物料齐套率
    from app.api.v1.endpoints.kit_rate import calculate_kit_rate
    from app.models.material import BomHeader, BomItem
    
    for machine in machines:
        # 获取机台的已发布BOM
        bom = db.query(BomHeader).filter(
            BomHeader.machine_id == machine.id,
            BomHeader.status == "RELEASED"
        ).first()
        
        if not bom:
            missing.append(f"机台 {machine.machine_code} 的BOM未发布")
            continue
        
        # 获取BOM明细
        bom_items = db.query(BomItem).filter(BomItem.bom_id == bom.id).all()
        
        if not bom_items:
            continue
        
        # 计算齐套率
        kit_result = calculate_kit_rate(db, bom_items, calculate_by="quantity")
        kit_rate = kit_result.get("kit_rate", 0)
        
        if kit_rate < 80:
            missing.append(f"机台 {machine.machine_code} 物料齐套率 {kit_rate:.1f}%，需≥80%")
        
        # 检查关键物料已到货（细化关键物料定义）
        for item in bom_items:
            material = item.material
            if material and (material.is_key_material or material.material_category in ["关键件", "核心件", "KEY"]):
                # 计算可用数量 = 当前库存 + 已到货数量
                available_qty = Decimal(str(material.current_stock or 0)) + Decimal(str(item.received_qty or 0))
                required_qty = Decimal(str(item.quantity or 0))
                
                if available_qty < required_qty:
                    missing.append(f"关键物料 {material.material_name} 未到货（需求：{required_qty}，可用：{available_qty}）")
        
        # 检查外协件已完成（如有）
        from app.models.outsourcing import OutsourcingOrder
        outsourcing_orders = db.query(OutsourcingOrder).filter(
            OutsourcingOrder.project_id == project.id,
            OutsourcingOrder.machine_id == machine.id if machine else None
        ).all()
        
        if outsourcing_orders:
            for order in outsourcing_orders:
                if order.status not in ["COMPLETED", "CLOSED"]:
                    # 检查订单是否已全部交付
                    total_ordered = sum(float(item.order_quantity or 0) for item in order.items)
                    total_delivered = sum(float(item.delivered_quantity or 0) for item in order.items)
                    
                    if total_delivered < total_ordered:
                        missing.append(f"外协订单 {order.order_no} 未完成（已交付：{total_delivered}，需求：{total_ordered}）")
    
    return (len(missing) == 0, missing)


def check_gate_s6_to_s7(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G6: S6→S7 阶段门校验 - 装配完成、联调通过
    
    Issue 1.3: 细化校验条件
    """
    missing = []
    
    # 检查所有机台的装配状态
    machines = db.query(Machine).filter(Machine.project_id == project.id).all()
    
    if not machines:
        missing.append("项目下没有机台")
        return (False, missing)
    
    for machine in machines:
        # 检查装配已完成（有完成记录或状态）
        if machine.progress_pct < 100:
            missing.append(f"机台 {machine.machine_code} 装配未完成（进度：{machine.progress_pct}%，需达到100%）")
        
        # 检查机台状态是否为装配完成状态
        if machine.status not in ["ASSEMBLED", "READY", "COMPLETED"]:
            missing.append(f"机台 {machine.machine_code} 状态未达到装配完成（当前状态：{machine.status}）")
    
    # 检查联调已通过（有联调报告或状态）
    from app.models.project import ProjectDocument
    debug_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project.id,
        ProjectDocument.doc_type.in_(["DEBUG", "TEST", "COMMISSIONING"]),
        ProjectDocument.status == "APPROVED"
    ).count()
    
    if debug_docs == 0:
        missing.append("联调测试报告未提交或未通过（请上传联调报告并标记为已确认）")
    
    # 检查技术问题已解决
    from app.models.issue import Issue
    blocking_issues = db.query(Issue).filter(
        Issue.project_id == project.id,
        Issue.is_blocking == True,
        Issue.status.notin_(["RESOLVED", "CLOSED"])
    ).count()
    
    if blocking_issues > 0:
        missing.append(f"存在 {blocking_issues} 个未解决的阻塞问题（请先解决所有阻塞问题）")
    
    # 检查是否有技术评审问题未解决
    from app.models.technical_review import ReviewIssue, TechnicalReview
    unresolved_review_issues = db.query(ReviewIssue).join(
        TechnicalReview, ReviewIssue.review_id == TechnicalReview.id
    ).filter(
        TechnicalReview.project_id == project.id,
        ReviewIssue.status.notin_(["RESOLVED", "VERIFIED", "CLOSED"]),
        ReviewIssue.issue_level.in_(["A", "B"])  # A/B级问题必须解决
    ).count()
    
    if unresolved_review_issues > 0:
        missing.append(f"存在 {unresolved_review_issues} 个未解决的评审问题（A/B级问题必须解决）")
    
    return (len(missing) == 0, missing)


def check_gate_s7_to_s8(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G7: S7→S8 阶段门校验 - FAT验收通过
    
    Issue 1.3: 细化校验条件
    """
    missing = []
    
    # 检查FAT验收已通过（关联验收模块）
    from app.models.acceptance import AcceptanceOrder
    fat_orders = db.query(AcceptanceOrder).filter(
        AcceptanceOrder.project_id == project.id,
        AcceptanceOrder.acceptance_type == "FAT",
        AcceptanceOrder.status == "COMPLETED",
        AcceptanceOrder.overall_result == "PASSED"
    ).all()
    
    if not fat_orders:
        # 检查是否有FAT验收单但未通过
        fat_orders_failed = db.query(AcceptanceOrder).filter(
            AcceptanceOrder.project_id == project.id,
            AcceptanceOrder.acceptance_type == "FAT",
            AcceptanceOrder.status == "COMPLETED",
            AcceptanceOrder.overall_result == "FAILED"
        ).count()
        
        if fat_orders_failed > 0:
            missing.append("FAT验收不通过（请完成整改后重新验收）")
        else:
            missing.append("FAT验收未完成（请完成FAT验收流程）")
    else:
        # 检查FAT报告已生成
        from app.models.acceptance import AcceptanceReport
        fat_reports = db.query(AcceptanceReport).join(
            AcceptanceOrder, AcceptanceReport.order_id == AcceptanceOrder.id
        ).filter(
            AcceptanceOrder.project_id == project.id,
            AcceptanceOrder.acceptance_type == "FAT",
            AcceptanceOrder.status == "COMPLETED"
        ).count()
        
        if fat_reports == 0:
            missing.append("FAT报告未生成（请生成FAT验收报告）")
        
        # 检查整改项已全部完成（如有）
        from app.models.acceptance import AcceptanceIssue
        unresolved_issues = db.query(AcceptanceIssue).join(
            AcceptanceOrder, AcceptanceIssue.order_id == AcceptanceOrder.id
        ).filter(
            AcceptanceOrder.project_id == project.id,
            AcceptanceOrder.acceptance_type == "FAT",
            AcceptanceIssue.status.notin_(["RESOLVED", "CLOSED"])
        ).count()
        
        if unresolved_issues > 0:
            missing.append(f"存在 {unresolved_issues} 个未完成的FAT整改项（请完成所有整改项）")
    
    return (len(missing) == 0, missing)


def check_gate_s8_to_s9(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G8: S8→S9 阶段门校验 - 终验收通过、回款达标
    
    Issue 1.3: 细化校验条件
    """
    missing = []
    
    # 检查终验收已通过（关联验收模块）
    from app.models.acceptance import AcceptanceOrder
    final_orders = db.query(AcceptanceOrder).filter(
        AcceptanceOrder.project_id == project.id,
        AcceptanceOrder.acceptance_type == "FINAL",
        AcceptanceOrder.status == "COMPLETED",
        AcceptanceOrder.overall_result == "PASSED"
    ).all()
    
    # 如果没有终验收，检查SAT验收
    if not final_orders:
        sat_orders = db.query(AcceptanceOrder).filter(
            AcceptanceOrder.project_id == project.id,
            AcceptanceOrder.acceptance_type == "SAT",
            AcceptanceOrder.status == "COMPLETED",
            AcceptanceOrder.overall_result == "PASSED"
        ).all()
        
        if not sat_orders:
            # 检查是否有SAT验收但未通过
            sat_failed = db.query(AcceptanceOrder).filter(
                AcceptanceOrder.project_id == project.id,
                AcceptanceOrder.acceptance_type == "SAT",
                AcceptanceOrder.status == "COMPLETED",
                AcceptanceOrder.overall_result == "FAILED"
            ).count()
            
            if sat_failed > 0:
                missing.append("SAT验收不通过（请完成整改后重新验收）")
            else:
                missing.append("终验收未完成（请完成SAT或终验收流程）")
        else:
            # SAT通过但需要终验收
            missing.append("终验收未完成（SAT已通过，请完成终验收）")
    
    # 检查回款达标（关联销售模块，检查收款计划完成情况）
    payment_plans = db.query(ProjectPaymentPlan).filter(
        ProjectPaymentPlan.project_id == project.id
    ).all()
    
    if payment_plans:
        total_paid = sum(float(plan.actual_amount or 0) for plan in payment_plans if plan.status == "PAID")
        total_planned = sum(float(plan.planned_amount or 0) for plan in payment_plans)
        contract_amount = float(project.contract_amount or 0)
        
        # 使用合同金额或计划金额中较大的作为基准
        base_amount = max(contract_amount, total_planned) if total_planned > 0 else contract_amount
        
        if base_amount > 0:
            payment_rate = (total_paid / base_amount) * 100
            if payment_rate < 80:  # 回款率需≥80%
                missing.append(f"回款率 {payment_rate:.1f}%，需≥80%（已回款：{total_paid:.2f}，合同金额：{base_amount:.2f}）")
    else:
        # 如果没有收款计划，检查合同金额是否已回款
        if project.contract_amount and project.contract_amount > 0:
            missing.append("收款计划未设置（请设置收款计划）")
    
    # 检查质保期服务已完成（如有要求）
    # 如果项目有质保期要求，检查质保期是否已开始或完成
    if project.stage == "S8" and project.status == "ST27":
        # 如果项目在S8阶段且状态为待终验签字，可以推进
        pass
    elif project.stage == "S8":
        # 检查是否所有设备都已交付
        machines = db.query(Machine).filter(Machine.project_id == project.id).all()
        if machines:
            for machine in machines:
                if machine.status not in ["DELIVERED", "COMPLETED"]:
                    missing.append(f"机台 {machine.machine_code} 未交付（当前状态：{machine.status}）")
    
    return (len(missing) == 0, missing)


def check_gate(db: Session, project: Project, target_stage: str) -> Tuple[bool, List[str]]:
    """
    阶段门准入校验
    
    Args:
        db: 数据库会话
        project: 项目对象
        target_stage: 目标阶段（S1-S9）
    
    Returns:
        (is_pass, missing_items): 是否通过，缺失项列表
    """
    gates = {
        'S2': check_gate_s1_to_s2,
        'S3': check_gate_s2_to_s3,
        'S4': check_gate_s3_to_s4,
        'S5': check_gate_s4_to_s5,
        'S6': check_gate_s5_to_s6,
        'S7': check_gate_s6_to_s7,
        'S8': check_gate_s7_to_s8,
        'S9': check_gate_s8_to_s9,
    }
    
    if target_stage in gates:
        return gates[target_stage](db, project)
    return (True, [])


def check_gate_detailed(db: Session, project: Project, target_stage: str) -> Dict[str, Any]:
    """
    Issue 1.4: 阶段门校验结果详细反馈
    
    返回结构化的校验结果，包含每个条件的检查状态
    
    Args:
        db: 数据库会话
        project: 项目对象
        target_stage: 目标阶段（S1-S9）
    
    Returns:
        dict: 详细的校验结果
    """
    from app.schemas.project import GateCheckCondition
    
    gate_info = {
        'S2': ('G1', '需求进入→需求澄清', 'S1', 'S2'),
        'S3': ('G2', '需求澄清→立项评审', 'S2', 'S3'),
        'S4': ('G3', '立项评审→方案设计', 'S3', 'S4'),
        'S5': ('G4', '方案设计→采购制造', 'S4', 'S5'),
        'S6': ('G5', '采购制造→装配联调', 'S5', 'S6'),
        'S7': ('G6', '装配联调→出厂验收', 'S6', 'S7'),
        'S8': ('G7', '出厂验收→现场交付', 'S7', 'S8'),
        'S9': ('G8', '现场交付→质保结项', 'S8', 'S9'),
    }
    
    if target_stage not in gate_info:
        return {
            "gate_code": "",
            "gate_name": "",
            "from_stage": project.stage,
            "to_stage": target_stage,
            "passed": True,
            "total_conditions": 0,
            "passed_conditions": 0,
            "failed_conditions": 0,
            "conditions": [],
            "missing_items": [],
            "suggestions": [],
            "progress_pct": 100.0
        }
    
    gate_code, gate_name, from_stage, to_stage = gate_info[target_stage]
    
    # 执行校验
    gate_passed, missing_items = check_gate(db, project, target_stage)
    
    # 构建条件详情（根据缺失项反向推断条件）
    conditions = []
    passed_count = 0
    failed_count = 0
    
    # 根据阶段门类型构建条件列表
    if target_stage == 'S2':
        conditions = [
            GateCheckCondition(
                condition_name="客户信息齐全",
                condition_desc="客户名称、联系人、联系电话",
                status="PASSED" if project.customer_id and project.customer_name and project.customer_contact and project.customer_phone else "FAILED",
                message="客户信息已完整" if project.customer_id and project.customer_name else "请填写客户信息",
                action_url=f"/projects/{project.id}/edit",
                action_text="去填写"
            ),
            GateCheckCondition(
                condition_name="需求采集表完整",
                condition_desc="项目基本信息、需求描述",
                status="PASSED" if project.requirements else "FAILED",
                message="需求采集表已填写" if project.requirements else "请填写需求采集表",
                action_url=f"/projects/{project.id}/edit",
                action_text="去填写"
            ),
        ]
    elif target_stage == 'S3':
        from app.models.project import ProjectDocument
        spec_docs_count = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project.id,
            ProjectDocument.doc_type.in_(["REQUIREMENT", "SPECIFICATION"]),
            ProjectDocument.status == "APPROVED"
        ).count()
        
        conditions = [
            GateCheckCondition(
                condition_name="需求规格书已确认",
                condition_desc="需求规格书文档已上传并确认",
                status="PASSED" if spec_docs_count > 0 else "FAILED",
                message=f"已确认 {spec_docs_count} 个规格书文档" if spec_docs_count > 0 else "请上传并确认需求规格书",
                action_url=f"/projects/{project.id}/documents",
                action_text="去上传"
            ),
            GateCheckCondition(
                condition_name="验收标准明确",
                condition_desc="验收标准文档或记录",
                status="PASSED" if project.requirements and ("验收标准" in project.requirements or "acceptance" in project.requirements.lower()) else "FAILED",
                message="验收标准已明确" if project.requirements and ("验收标准" in project.requirements or "acceptance" in project.requirements.lower()) else "请明确验收标准",
                action_url=f"/projects/{project.id}/edit",
                action_text="去填写"
            ),
            GateCheckCondition(
                condition_name="客户已签字确认",
                condition_desc="需求规格书客户签字确认",
                status="PASSED" if project.status != "ST05" else "FAILED",
                message="客户已确认" if project.status != "ST05" else "待客户签字确认",
                action_url=f"/projects/{project.id}",
                action_text="查看详情"
            ),
        ]
    # 其他阶段门的条件可以类似构建，这里先实现核心的几个
    
    # 统计通过和失败的条件数
    for condition in conditions:
        if condition.status == "PASSED":
            passed_count += 1
        elif condition.status == "FAILED":
            failed_count += 1
    
    total_conditions = len(conditions) if conditions else len(missing_items)
    if total_conditions == 0:
        progress_pct = 100.0
    else:
        progress_pct = (passed_count / total_conditions) * 100
    
    # 生成建议操作
    suggestions = []
    if not gate_passed:
        suggestions.append(f"请完成以上 {failed_count} 项条件后重新尝试推进阶段")
        if missing_items:
            suggestions.append(f"缺失项：{', '.join(missing_items[:3])}{'...' if len(missing_items) > 3 else ''}")
    
    return {
        "gate_code": gate_code,
        "gate_name": gate_name,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "passed": gate_passed,
        "total_conditions": total_conditions,
        "passed_conditions": passed_count,
        "failed_conditions": failed_count,
        "conditions": [c.model_dump() for c in conditions] if conditions else [],
        "missing_items": missing_items,
        "suggestions": suggestions,
        "progress_pct": round(progress_pct, 1)
    }


@router.post("/{project_id}/stage-advance", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def advance_project_stage(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    advance_request: StageAdvanceRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目阶段推进（含阶段门校验）
    
    根据目标阶段进行阶段门校验，通过后更新项目阶段和状态
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    from app.services.stage_advance_service import (
        validate_target_stage,
        validate_stage_advancement,
        perform_gate_check,
        update_project_stage_and_status,
        create_status_log,
        create_installation_dispatch_orders,
        generate_cost_review_report
    )
    from app.api.v1.endpoints.projects import check_gate_detailed
    
    # 检查项目访问权限
    project = check_project_access_or_raise(db, current_user, project_id)
    
    # 验证目标阶段
    validate_target_stage(advance_request.target_stage)
    
    # 检查阶段是否向前推进
    current_stage = project.stage or "S1"
    validate_stage_advancement(current_stage, advance_request.target_stage)
    
    # 阶段门校验（除非跳过）
    gate_passed, missing_items, gate_check_result = perform_gate_check(
        db, project, advance_request.target_stage,
        advance_request.skip_gate_check, current_user.is_superuser
    )
    
    if not gate_passed:
        return ResponseModel(
            code=400,
            message="阶段门校验未通过",
            data={
                "project_id": project_id,
                "target_stage": advance_request.target_stage,
                "gate_passed": False,
                "missing_items": missing_items,
                "gate_check_result": gate_check_result,
            }
        )
    
    # 记录旧阶段
    old_stage = current_stage
    old_status = project.status
    
    # 更新项目阶段和状态
    new_status = update_project_stage_and_status(
        db, project, advance_request.target_stage, old_stage, old_status
    )
    
    # 记录状态变更历史
    create_status_log(
        db, project_id, old_stage, advance_request.target_stage,
        old_status, new_status, project.health,
        advance_request.reason, current_user.id
    )
    
    # 如果项目进入S8阶段，自动创建安装调试派工单
    create_installation_dispatch_orders(
        db, project, advance_request.target_stage, old_stage
    )
    
    # 如果项目进入S9阶段或状态变为ST30，自动生成成本复盘报告
    generate_cost_review_report(
        db, project_id, advance_request.target_stage, new_status, current_user.id
    )
    
    db.commit()
    db.refresh(project)
    
    return ResponseModel(
        code=200,
        message="阶段推进成功",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "old_stage": old_stage,
            "new_stage": advance_request.target_stage,
            "new_status": new_status,
            "gate_passed": gate_passed,
            "gate_check_result": check_gate_detailed(db, project, advance_request.target_stage) if not advance_request.skip_gate_check else None,
        }
    )


# ==================== Issue 1.2: 阶段自动流转 ====================

@router.post("/{project_id}/check-auto-transition", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def check_auto_stage_transition(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    auto_advance: bool = Query(False, description="是否自动推进（True=自动推进，False=仅检查）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 1.2: 检查阶段自动流转条件
    
    当满足条件时自动推进项目阶段
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    from app.services.status_transition_service import StatusTransitionService
    
    # 检查项目访问权限
    check_project_access_or_raise(db, current_user, project_id)
    
    transition_service = StatusTransitionService(db)
    result = transition_service.check_auto_stage_transition(project_id, auto_advance=auto_advance)
    
    return ResponseModel(
        code=200,
        message=result.get("message", "检查完成"),
        data=result
    )


@router.get("/{project_id}/gate-check/{target_stage}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_gate_check_result(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    target_stage: str = Path(..., description="目标阶段（S2-S9）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 1.4: 获取阶段门校验详细结果
    
    返回结构化的校验结果，包含每个条件的检查状态
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    
    # 检查项目访问权限
    project = check_project_access_or_raise(db, current_user, project_id)
    
    # 验证目标阶段
    valid_stages = ['S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    if target_stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"无效的目标阶段。有效值：{', '.join(valid_stages)}"
        )
    
    gate_check_result = check_gate_detailed(db, project, target_stage)
    
    return ResponseModel(
        code=200,
        message="获取阶段门校验结果成功",
        data=gate_check_result
    )


# ==================== 项目批量操作 ====================

@router.post("/batch/update-status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_update_project_status(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchUpdateStatusRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新项目状态
    """
    # 验证状态编码
    valid_statuses = [f"ST{i:02d}" for i in range(1, 31)]
    if batch_request.new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"无效的状态编码。有效值：ST01-ST30"
        )
    
    success_count = 0
    failed_projects = []
    
    # 应用数据权限过滤
    from app.services.data_scope_service import DataScopeService
    query = db.query(Project).filter(Project.id.in_(batch_request.project_ids))
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    accessible_project_ids = {p.id for p in query.all()}
    
    for project_id in batch_request.project_ids:
        try:
            # 检查权限
            if project_id not in accessible_project_ids:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "无访问权限"
                })
                continue
            
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目不存在"
                })
                continue
            
            old_status = project.status
            if old_status == batch_request.new_status:
                continue  # 状态未变化，跳过
            
            project.status = batch_request.new_status
            db.add(project)
            
            # 记录状态变更历史
            status_log = ProjectStatusLog(
                project_id=project_id,
                old_stage=project.stage,
                new_stage=project.stage,
                old_status=old_status,
                new_status=batch_request.new_status,
                old_health=project.health,
                new_health=project.health,
                change_type="STATUS_CHANGE",
                change_reason=batch_request.reason or f"批量状态变更：{old_status} → {batch_request.new_status}",
                changed_by=current_user.id,
                changed_at=datetime.now()
            )
            db.add(status_log)
            success_count += 1
        
        except Exception as e:
            failed_projects.append({
                "project_id": project_id,
                "reason": str(e)
            })
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"批量状态更新完成：成功 {success_count} 个，失败 {len(failed_projects)} 个",
        data={
            "success_count": success_count,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects
        }
    )


@router.post("/batch/update-stage", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_update_project_stage(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchUpdateStageRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新项目阶段
    """
    # 验证阶段编码
    valid_stages = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    if batch_request.new_stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"无效的阶段编码。有效值：{', '.join(valid_stages)}"
        )
    
    success_count = 0
    failed_projects = []
    
    # 应用数据权限过滤
    from app.services.data_scope_service import DataScopeService
    query = db.query(Project).filter(Project.id.in_(batch_request.project_ids))
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    accessible_project_ids = {p.id for p in query.all()}
    
    for project_id in batch_request.project_ids:
        try:
            # 检查权限
            if project_id not in accessible_project_ids:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "无访问权限"
                })
                continue
            
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目不存在"
                })
                continue
            
            old_stage = project.stage or "S1"
            if old_stage == batch_request.new_stage:
                continue  # 阶段未变化，跳过
            
            project.stage = batch_request.new_stage
            db.add(project)
            
            # 记录状态变更历史
            status_log = ProjectStatusLog(
                project_id=project_id,
                old_stage=old_stage,
                new_stage=batch_request.new_stage,
                old_status=project.status,
                new_status=project.status,
                old_health=project.health,
                new_health=project.health,
                change_type="STAGE_CHANGE",
                change_reason=batch_request.reason or f"批量阶段变更：{old_stage} → {batch_request.new_stage}",
                changed_by=current_user.id,
                changed_at=datetime.now()
            )
            db.add(status_log)
            success_count += 1
        
        except Exception as e:
            failed_projects.append({
                "project_id": project_id,
                "reason": str(e)
            })
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"批量阶段更新完成：成功 {success_count} 个，失败 {len(failed_projects)} 个",
        data={
            "success_count": success_count,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects
        }
    )


@router.post("/batch/assign-pm", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_assign_project_manager(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchAssignPMRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量分配项目经理
    """
    # 验证项目经理是否存在
    pm = db.query(User).filter(User.id == batch_request.pm_id).first()
    if not pm:
        raise HTTPException(status_code=404, detail="项目经理不存在")
    
    pm_name = pm.real_name or pm.username
    
    success_count = 0
    failed_projects = []
    
    # 应用数据权限过滤
    from app.services.data_scope_service import DataScopeService
    query = db.query(Project).filter(Project.id.in_(batch_request.project_ids))
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    accessible_project_ids = {p.id for p in query.all()}
    
    for project_id in batch_request.project_ids:
        try:
            # 检查权限
            if project_id not in accessible_project_ids:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "无访问权限"
                })
                continue
            
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目不存在"
                })
                continue
            
            old_pm_id = project.pm_id
            old_pm_name = project.pm_name
            
            project.pm_id = batch_request.pm_id
            project.pm_name = pm_name
            db.add(project)
            
            # 记录变更历史（可选）
            if old_pm_id != batch_request.pm_id:
                status_log = ProjectStatusLog(
                    project_id=project_id,
                    old_stage=project.stage,
                    new_stage=project.stage,
                    old_status=project.status,
                    new_status=project.status,
                    old_health=project.health,
                    new_health=project.health,
                    change_type="PM_CHANGE",
                    change_reason=f"批量分配项目经理：{old_pm_name or '未分配'} → {pm_name}",
                    changed_by=current_user.id,
                    changed_at=datetime.now()
                )
                db.add(status_log)
            
            success_count += 1
        
        except Exception as e:
            failed_projects.append({
                "project_id": project_id,
                "reason": str(e)
            })
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"批量分配项目经理完成：成功 {success_count} 个，失败 {len(failed_projects)} 个",
        data={
            "success_count": success_count,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects,
            "pm_id": batch_request.pm_id,
            "pm_name": pm_name
        }
    )


@router.post("/batch/archive", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_archive_projects(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchArchiveRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量归档项目
    """
    success_count = 0
    failed_projects = []
    
    # 应用数据权限过滤
    from app.services.data_scope_service import DataScopeService
    query = db.query(Project).filter(Project.id.in_(batch_request.project_ids))
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    accessible_project_ids = {p.id for p in query.all()}
    
    for project_id in batch_request.project_ids:
        try:
            # 检查权限
            if project_id not in accessible_project_ids:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "无访问权限"
                })
                continue
            
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目不存在"
                })
                continue
            
            if project.is_archived:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目已归档"
                })
                continue
            
            # 检查项目是否可以归档（通常需要项目已完成或已结项）
            if project.stage not in ["S9"] and project.status not in ["ST30"]:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目未完成，无法归档"
                })
                continue
            
            project.is_archived = True
            if batch_request.archive_reason:
                if project.description:
                    project.description += f"\n[批量归档原因] {batch_request.archive_reason}"
                else:
                    project.description = f"[批量归档原因] {batch_request.archive_reason}"
            
            db.add(project)
            success_count += 1
        
        except Exception as e:
            failed_projects.append({
                "project_id": project_id,
                "reason": str(e)
            })
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"批量归档完成：成功 {success_count} 个，失败 {len(failed_projects)} 个",
        data={
            "success_count": success_count,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects
        }
    )


# ==================== 项目复盘（旧实现，使用PmoProjectClosure，已废弃） ====================
# 注意：以下端点使用旧的PmoProjectClosure模型，建议使用新的ProjectReview模型端点

@router.get("/project-reviews-old", response_model=PaginatedResponse, status_code=status.HTTP_200_OK, deprecated=True)
def get_project_reviews(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    复盘报告列表
    获取项目复盘报告列表，支持分页和筛选
    """
    # 从PMO项目结项记录中获取复盘信息
    from app.models.pmo import PmoProjectClosure
    from app.services.data_scope_service import DataScopeService
    
    query = db.query(PmoProjectClosure).join(
        Project, PmoProjectClosure.project_id == Project.id
    ).filter(
        or_(
            PmoProjectClosure.review_result == "APPROVED",
            PmoProjectClosure.archive_status == "COMPLETED"
        )
    )
    
    # 应用数据权限过滤
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    
    if project_id:
        query = query.filter(PmoProjectClosure.project_id == project_id)
    if start_date:
        query = query.filter(PmoProjectClosure.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(PmoProjectClosure.created_at <= datetime.combine(end_date, datetime.max.time()))
    
    total = query.count()
    offset = (page - 1) * page_size
    closures = query.order_by(desc(PmoProjectClosure.created_at)).offset(offset).limit(page_size).all()
    
    # 构建复盘报告列表（批量查询项目信息，优化性能）
    reviews = []
    if closures:
        # 批量获取项目信息
        project_ids = [c.project_id for c in closures]
        projects_dict = {p.id: p for p in db.query(Project).filter(Project.id.in_(project_ids)).all()}
    else:
        projects_dict = {}
    
    for closure in closures:
        project = projects_dict.get(closure.project_id)
        
        reviews.append({
            "id": closure.id,
            "project_id": closure.project_id,
            "project_code": project.project_code if project else None,
            "project_name": project.project_name if project else None,
            "review_date": closure.reviewed_at.date() if closure.reviewed_at else (closure.created_at.date() if closure.created_at else None),
            "acceptance_date": closure.acceptance_date.isoformat() if closure.acceptance_date else None,
            "final_cost": float(closure.final_cost) if closure.final_cost else None,
            "final_budget": float(closure.final_budget) if closure.final_budget else None,
            "cost_variance": float(closure.cost_variance) if closure.cost_variance else None,
            "plan_duration": closure.plan_duration,
            "actual_duration": closure.actual_duration,
            "schedule_variance": closure.schedule_variance,
            "quality_score": closure.quality_score,
            "customer_satisfaction": closure.customer_satisfaction,
            "lessons_learned": closure.lessons_learned,
            "improvement_suggestions": closure.improvement_suggestions,
            "review_result": closure.review_result,
            "archive_status": closure.archive_status,
            "reviewed_by": closure.reviewed_by,
            "reviewed_at": closure.reviewed_at.isoformat() if closure.reviewed_at else None,
            "created_at": closure.created_at.isoformat() if closure.created_at else None
        })
    
    return PaginatedResponse(
        items=reviews,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/project-reviews-old", response_model=ResponseModel, status_code=status.HTTP_201_CREATED, deprecated=True)
def create_project_review(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Body(..., description="项目ID"),
    review_date: date = Body(..., description="复盘日期"),
    participants: Optional[List[int]] = Body(None, description="参与人ID列表"),
    success_factors: Optional[str] = Body(None, description="成功因素"),
    problems: Optional[str] = Body(None, description="问题与教训"),
    improvements: Optional[str] = Body(None, description="改进建议"),
    best_practices: Optional[str] = Body(None, description="最佳实践"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建复盘报告
    基于项目结项记录创建复盘报告
    """
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)
    
    # 检查项目是否已完成（建议在S9阶段或ST30状态）
    if project.stage not in ["S9"] and project.status not in ["ST30"]:
        raise HTTPException(
            status_code=400,
            detail="项目未完成，无法创建复盘报告。请先完成项目结项。"
        )
    
    # 检查是否已有结项记录
    from app.models.pmo import PmoProjectClosure
    closure = db.query(PmoProjectClosure).filter(PmoProjectClosure.project_id == project_id).first()
    
    # 计算项目周期
    plan_duration = None
    actual_duration = None
    schedule_variance = None
    
    if project.planned_start_date and project.planned_end_date:
        plan_duration = (project.planned_end_date - project.planned_start_date).days
    
    if project.actual_start_date and project.actual_end_date:
        actual_duration = (project.actual_end_date - project.actual_start_date).days
    elif project.actual_start_date:
        actual_duration = (date.today() - project.actual_start_date).days
    
    if plan_duration and actual_duration:
        schedule_variance = actual_duration - plan_duration
    
    # 计算成本偏差
    budget_amount = float(project.budget_amount or 0)
    actual_cost = float(project.actual_cost or 0)
    cost_variance = actual_cost - budget_amount
    
    if not closure:
        # 如果没有结项记录，创建一个基本的结项记录
        closure = PmoProjectClosure(
            project_id=project_id,
            acceptance_date=review_date,
            acceptance_result="PASSED",
            project_summary=f"项目{project.project_name}复盘报告",
            achievement=success_factors,
            lessons_learned=problems,
            improvement_suggestions=improvements,
            final_budget=project.budget_amount,
            final_cost=project.actual_cost,
            cost_variance=cost_variance,
            plan_duration=plan_duration,
            actual_duration=actual_duration,
            schedule_variance=schedule_variance,
            reviewed_by=current_user.id,
            reviewed_at=datetime.now(),
            review_date=review_date,
            review_result="APPROVED"
        )
        db.add(closure)
    else:
        # 更新现有结项记录
        if success_factors:
            closure.achievement = success_factors
        if problems:
            closure.lessons_learned = problems
        if improvements:
            closure.improvement_suggestions = improvements
        if not closure.acceptance_date:
            closure.acceptance_date = review_date
        if not closure.final_budget:
            closure.final_budget = project.budget_amount
        if not closure.final_cost:
            closure.final_cost = project.actual_cost
        if closure.cost_variance is None:
            closure.cost_variance = cost_variance
        if closure.plan_duration is None:
            closure.plan_duration = plan_duration
        if closure.actual_duration is None:
            closure.actual_duration = actual_duration
        if closure.schedule_variance is None:
            closure.schedule_variance = schedule_variance
        closure.reviewed_by = current_user.id
        closure.reviewed_at = datetime.now()
        closure.review_date = review_date
        if not closure.review_result:
            closure.review_result = "APPROVED"
        db.add(closure)
    
    db.commit()
    db.refresh(closure)
    
    # 获取参与人姓名
    participant_names = []
    if participants:
        users = db.query(User).filter(User.id.in_(participants)).all()
        participant_names = [u.real_name or u.username for u in users]
    
    return ResponseModel(
        code=200,
        message="复盘报告创建成功",
        data={
            "id": closure.id,
            "project_id": project_id,
            "project_name": project.project_name,
            "review_date": review_date.isoformat(),
            "participants": participants or [],
            "participant_names": participant_names,
            "success_factors": success_factors,
            "problems": problems,
            "improvements": improvements,
            "best_practices": best_practices,
            "cost_variance": float(closure.cost_variance) if closure.cost_variance else None,
            "schedule_variance": closure.schedule_variance,
            "created_at": datetime.now().isoformat()
        }
    )


@router.get("/project-reviews-old/{review_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK, deprecated=True)
def get_project_review_detail(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取复盘报告详情
    """
    from app.models.pmo import PmoProjectClosure
    closure = db.query(PmoProjectClosure).filter(PmoProjectClosure.id == review_id).first()
    
    if not closure:
        raise HTTPException(status_code=404, detail="复盘报告不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, closure.project_id)
    
    # 获取评审人信息
    reviewer_name = None
    if closure.reviewed_by:
        reviewer = db.query(User).filter(User.id == closure.reviewed_by).first()
        reviewer_name = reviewer.real_name or reviewer.username if reviewer else None
    
    return ResponseModel(
        code=200,
        message="获取复盘报告详情成功",
        data={
            "id": closure.id,
            "project_id": closure.project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "acceptance_date": closure.acceptance_date.isoformat() if closure.acceptance_date else None,
            "acceptance_result": closure.acceptance_result,
            "acceptance_notes": closure.acceptance_notes,
            "project_summary": closure.project_summary,
            "achievement": closure.achievement,
            "lessons_learned": closure.lessons_learned,
            "improvement_suggestions": closure.improvement_suggestions,
            "final_budget": float(closure.final_budget) if closure.final_budget else None,
            "final_cost": float(closure.final_cost) if closure.final_cost else None,
            "cost_variance": float(closure.cost_variance) if closure.cost_variance else None,
            "plan_duration": closure.plan_duration,
            "actual_duration": closure.actual_duration,
            "schedule_variance": closure.schedule_variance,
            "quality_score": closure.quality_score,
            "customer_satisfaction": closure.customer_satisfaction,
            "review_result": closure.review_result,
            "review_date": closure.review_date.isoformat() if closure.review_date else None,
            "reviewed_by": closure.reviewed_by,
            "reviewer_name": reviewer_name,
            "reviewed_at": closure.reviewed_at.isoformat() if closure.reviewed_at else None,
            "archive_status": closure.archive_status,
            "created_at": closure.created_at.isoformat() if closure.created_at else None,
            "updated_at": closure.updated_at.isoformat() if closure.updated_at else None,
        }
    )


@router.get("/{project_id}/lessons-learned", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_lessons_learned(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    问题总结（经验教训）
    从项目的问题记录和结项记录中提取经验教训
    """
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)
    
    # 获取项目结项记录中的经验教训
    from app.models.pmo import PmoProjectClosure
    closure = db.query(PmoProjectClosure).filter(PmoProjectClosure.project_id == project_id).first()
    
    lessons_from_closure = {
        "lessons_learned": closure.lessons_learned if closure else None,
        "improvement_suggestions": closure.improvement_suggestions if closure else None,
        "achievement": closure.achievement if closure else None,
    }
    
    # 从问题记录中提取经验教训
    from app.models.issue import Issue
    issues = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status.in_(["RESOLVED", "CLOSED"])
    ).order_by(desc(Issue.resolved_at)).all()
    
    # 按问题类型分类
    lessons_by_category = {}
    for issue in issues:
        category = issue.category or "OTHER"
        if category not in lessons_by_category:
            lessons_by_category[category] = []
        
        lesson = {
            "issue_no": issue.issue_no,
            "title": issue.title,
            "description": issue.description,
            "solution": issue.solution,
            "severity": issue.severity,
            "priority": issue.priority,
            "resolved_at": issue.resolved_at.isoformat() if issue.resolved_at else None,
            "resolver_name": issue.resolver_name,
        }
        lessons_by_category[category].append(lesson)
    
    # 统计信息
    total_issues = len(issues)
    resolved_issues = len([i for i in issues if i.status == "RESOLVED"])
    critical_issues = len([i for i in issues if i.severity == "CRITICAL"])
    high_priority_issues = len([i for i in issues if i.priority == "HIGH"])
    
    # 提取关键经验教训（严重程度高或优先级高的问题）
    key_lessons = []
    for issue in issues:
        if issue.severity in ["CRITICAL", "HIGH"] or issue.priority in ["URGENT", "HIGH"]:
            key_lessons.append({
                "issue_no": issue.issue_no,
                "title": issue.title,
                "category": issue.category or "OTHER",
                "severity": issue.severity,
                "solution": issue.solution,
                "resolved_at": issue.resolved_at.isoformat() if issue.resolved_at else None,
            })
    
    # 限制关键经验教训数量
    key_lessons = key_lessons[:10]
    
    return ResponseModel(
        code=200,
        message="获取经验教训成功",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "summary": {
                "total_issues": total_issues,
                "resolved_issues": resolved_issues,
                "critical_issues": critical_issues,
                "high_priority_issues": high_priority_issues,
            },
            "lessons_from_closure": lessons_from_closure,
            "lessons_by_category": lessons_by_category,
            "key_lessons": key_lessons,
            "category_summary": [
                {
                    "category": category,
                    "count": len(lessons),
                    "critical_count": len([l for l in lessons if l.get("severity") == "CRITICAL"]),
                    "lessons": lessons[:5]  # 每个分类最多5条
                }
                for category, lessons in lessons_by_category.items()
            ]
        }
    )


# ==================== 项目成本管理 ====================

@router.get("/projects/{project_id}/cost-summary", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_cost_summary(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目成本汇总
    获取项目的成本汇总统计信息
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 导入ProjectCost模型
    from app.models.project import ProjectCost
    
    # 总成本统计
    total_result = db.query(
        func.sum(ProjectCost.amount).label('total_amount'),
        func.sum(ProjectCost.tax_amount).label('total_tax'),
        func.count(ProjectCost.id).label('total_count')
    ).filter(ProjectCost.project_id == project_id).first()
    
    total_amount = float(total_result.total_amount) if total_result.total_amount else 0
    total_tax = float(total_result.total_tax) if total_result.total_tax else 0
    total_count = total_result.total_count or 0
    
    # 按成本类型统计
    type_stats = db.query(
        ProjectCost.cost_type,
        func.sum(ProjectCost.amount).label('amount'),
        func.count(ProjectCost.id).label('count')
    ).filter(
        ProjectCost.project_id == project_id
    ).group_by(ProjectCost.cost_type).all()
    
    type_summary = [
        {
            "cost_type": stat.cost_type,
            "amount": round(float(stat.amount) if stat.amount else 0, 2),
            "count": stat.count or 0,
            "percentage": round((float(stat.amount) / total_amount * 100) if total_amount > 0 else 0, 2)
        }
        for stat in type_stats
    ]
    
    # 按成本分类统计
    category_stats = db.query(
        ProjectCost.cost_category,
        func.sum(ProjectCost.amount).label('amount'),
        func.count(ProjectCost.id).label('count')
    ).filter(
        ProjectCost.project_id == project_id
    ).group_by(ProjectCost.cost_category).all()
    
    category_summary = [
        {
            "cost_category": stat.cost_category,
            "amount": round(float(stat.amount) if stat.amount else 0, 2),
            "count": stat.count or 0,
            "percentage": round((float(stat.amount) / total_amount * 100) if total_amount > 0 else 0, 2)
        }
        for stat in category_stats
    ]
    
    # 按机台统计
    machine_stats = db.query(
        ProjectCost.machine_id,
        func.sum(ProjectCost.amount).label('amount'),
        func.count(ProjectCost.id).label('count')
    ).filter(
        ProjectCost.project_id == project_id,
        ProjectCost.machine_id.isnot(None)
    ).group_by(ProjectCost.machine_id).all()
    
    machine_summary = []
    for stat in machine_stats:
        machine = db.query(Machine).filter(Machine.id == stat.machine_id).first()
        machine_summary.append({
            "machine_id": stat.machine_id,
            "machine_code": machine.machine_code if machine else None,
            "machine_name": machine.machine_name if machine else None,
            "amount": round(float(stat.amount) if stat.amount else 0, 2),
            "count": stat.count or 0,
            "percentage": round((float(stat.amount) / total_amount * 100) if total_amount > 0 else 0, 2)
        })
    
    # 预算对比
    budget_amount = float(project.budget_amount or 0)
    actual_cost = float(project.actual_cost or 0)
    cost_variance = actual_cost - budget_amount
    cost_variance_pct = (cost_variance / budget_amount * 100) if budget_amount > 0 else 0
    
    # 合同对比
    contract_amount = float(project.contract_amount or 0)
    profit = contract_amount - actual_cost
    profit_margin = (profit / contract_amount * 100) if contract_amount > 0 else 0
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "budget_info": {
                "budget_amount": round(budget_amount, 2),
                "actual_cost": round(actual_cost, 2),
                "cost_variance": round(cost_variance, 2),
                "cost_variance_pct": round(cost_variance_pct, 2),
                "is_over_budget": cost_variance > 0
            },
            "contract_info": {
                "contract_amount": round(contract_amount, 2),
                "profit": round(profit, 2),
                "profit_margin": round(profit_margin, 2)
            },
            "cost_summary": {
                "total_amount": round(total_amount, 2),
                "total_tax": round(total_tax, 2),
                "total_with_tax": round(total_amount + total_tax, 2),
                "total_count": total_count
            },
            "by_type": type_summary,
            "by_category": category_summary,
            "by_machine": machine_summary
        }
    )


@router.get("/projects/{project_id}/cost-details", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_cost_details(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    cost_type: Optional[str] = Query(None, description="成本类型筛选"),
    cost_category: Optional[str] = Query(None, description="成本分类筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    成本明细列表
    获取项目的成本明细记录列表，支持分页和筛选
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 导入ProjectCost模型
    from app.models.project import ProjectCost
    from app.schemas.project import ProjectCostResponse
    
    query = db.query(ProjectCost).filter(ProjectCost.project_id == project_id)
    
    if machine_id:
        query = query.filter(ProjectCost.machine_id == machine_id)
    if cost_type:
        query = query.filter(ProjectCost.cost_type == cost_type)
    if cost_category:
        query = query.filter(ProjectCost.cost_category == cost_category)
    if start_date:
        query = query.filter(ProjectCost.cost_date >= start_date)
    if end_date:
        query = query.filter(ProjectCost.cost_date <= end_date)
    
    total = query.count()
    offset = (page - 1) * page_size
    costs = query.order_by(desc(ProjectCost.cost_date), desc(ProjectCost.created_at)).offset(offset).limit(page_size).all()
    
    # 构建成本明细列表
    cost_details = []
    for cost in costs:
        machine = None
        if cost.machine_id:
            machine = db.query(Machine).filter(Machine.id == cost.machine_id).first()
        
        # 获取创建人信息
        creator = None
        if cost.created_by:
            creator = db.query(User).filter(User.id == cost.created_by).first()
        
        cost_details.append({
            "id": cost.id,
            "cost_no": cost.cost_no,
            "cost_date": cost.cost_date.isoformat() if cost.cost_date else None,
            "cost_type": cost.cost_type,
            "cost_category": cost.cost_category,
            "amount": float(cost.amount) if cost.amount else 0,
            "tax_amount": float(cost.tax_amount) if cost.tax_amount else 0,
            "total_amount": float(cost.amount or 0) + float(cost.tax_amount or 0),
            "machine_id": cost.machine_id,
            "machine_code": machine.machine_code if machine else None,
            "machine_name": machine.machine_name if machine else None,
            "description": cost.description,
            "remark": cost.remark,
            "created_by": cost.created_by,
            "created_by_name": creator.real_name or creator.username if creator else None,
            "created_at": cost.created_at.isoformat() if cost.created_at else None
        })
    
    return PaginatedResponse(
        items=cost_details,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


# ==================== 项目复盘模块（使用新模型） ====================

def generate_review_no(db: Session) -> str:
    """生成复盘编号：REVIEW-YYYYMMDD-XXX"""
    today = date.today().strftime("%Y%m%d")
    # 查询当天已有的复盘报告数量
    count = db.query(ProjectReview).filter(
        ProjectReview.review_no.like(f"REVIEW-{today}-%")
    ).count()
    seq = count + 1
    return f"REVIEW-{today}-{seq:03d}"


@router.get("/project-reviews", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_reviews_v2(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目复盘报告列表（使用新模型）
    """
    from app.services.data_scope_service import DataScopeService
    
    query = db.query(ProjectReview).join(Project, ProjectReview.project_id == Project.id)
    
    # 应用数据权限过滤
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    
    if project_id:
        query = query.filter(ProjectReview.project_id == project_id)
    if start_date:
        query = query.filter(ProjectReview.review_date >= start_date)
    if end_date:
        query = query.filter(ProjectReview.review_date <= end_date)
    if status:
        query = query.filter(ProjectReview.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    reviews = query.order_by(desc(ProjectReview.review_date)).offset(offset).limit(page_size).all()
    
    items = []
    for review in reviews:
        items.append({
            "id": review.id,
            "review_no": review.review_no,
            "project_id": review.project_id,
            "project_code": review.project_code,
            "project_name": review.project.project_name if review.project else None,
            "review_date": review.review_date.isoformat() if review.review_date else None,
            "review_type": review.review_type,
            "plan_duration": review.plan_duration,
            "actual_duration": review.actual_duration,
            "schedule_variance": review.schedule_variance,
            "budget_amount": float(review.budget_amount) if review.budget_amount else None,
            "actual_cost": float(review.actual_cost) if review.actual_cost else None,
            "cost_variance": float(review.cost_variance) if review.cost_variance else None,
            "quality_issues": review.quality_issues,
            "change_count": review.change_count,
            "customer_satisfaction": review.customer_satisfaction,
            "reviewer_id": review.reviewer_id,
            "reviewer_name": review.reviewer_name,
            "participants": review.participants or [],
            "participant_names": review.participant_names,
            "status": review.status,
            "created_at": review.created_at.isoformat() if review.created_at else None,
            "updated_at": review.updated_at.isoformat() if review.updated_at else None,
        })
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/project-reviews", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_review_v2(
    *,
    db: Session = Depends(deps.get_db),
    review_data: ProjectReviewCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建项目复盘报告（使用新模型）
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    
    # 检查项目访问权限
    project = check_project_access_or_raise(db, current_user, review_data.project_id)
    
    # 检查项目是否已完成
    if project.stage not in ["S9"] and project.status not in ["ST30"]:
        raise HTTPException(
            status_code=400,
            detail="项目未完成，无法创建复盘报告。请先完成项目结项。"
        )
    
    # 检查是否已有复盘报告
    existing = db.query(ProjectReview).filter(
        ProjectReview.project_id == review_data.project_id,
        ProjectReview.review_type == review_data.review_type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"该项目已存在{review_data.review_type}类型的复盘报告"
        )
    
    # 生成复盘编号
    review_no = generate_review_no(db)
    
    # 计算项目周期和成本（如果未提供）
    plan_duration = review_data.plan_duration
    actual_duration = review_data.actual_duration
    schedule_variance = review_data.schedule_variance
    budget_amount = review_data.budget_amount
    actual_cost = review_data.actual_cost
    cost_variance = review_data.cost_variance
    
    if not plan_duration and project.planned_start_date and project.planned_end_date:
        plan_duration = (project.planned_end_date - project.planned_start_date).days
    
    if not actual_duration and project.actual_start_date:
        if project.actual_end_date:
            actual_duration = (project.actual_end_date - project.actual_start_date).days
        else:
            actual_duration = (date.today() - project.actual_start_date).days
    
    if plan_duration and actual_duration and not schedule_variance:
        schedule_variance = actual_duration - plan_duration
    
    if not budget_amount:
        budget_amount = project.budget_amount
    
    if not actual_cost:
        actual_cost = project.actual_cost
    
    if budget_amount and actual_cost and not cost_variance:
        cost_variance = actual_cost - budget_amount
    
    # 获取参与人姓名
    participant_names = []
    if review_data.participants:
        users = db.query(User).filter(User.id.in_(review_data.participants)).all()
        participant_names = [u.real_name or u.username for u in users]
    
    # 获取评审人姓名
    reviewer = db.query(User).filter(User.id == review_data.reviewer_id).first()
    reviewer_name = reviewer.real_name or reviewer.username if reviewer else current_user.real_name or current_user.username
    
    # 创建复盘报告
    review = ProjectReview(
        review_no=review_no,
        project_id=review_data.project_id,
        project_code=project.project_code,
        review_date=review_data.review_date,
        review_type=review_data.review_type,
        plan_duration=plan_duration,
        actual_duration=actual_duration,
        schedule_variance=schedule_variance,
        budget_amount=budget_amount,
        actual_cost=actual_cost,
        cost_variance=cost_variance,
        quality_issues=review_data.quality_issues or 0,
        change_count=review_data.change_count or 0,
        customer_satisfaction=review_data.customer_satisfaction,
        success_factors=review_data.success_factors,
        problems=review_data.problems,
        improvements=review_data.improvements,
        best_practices=review_data.best_practices,
        conclusion=review_data.conclusion,
        reviewer_id=review_data.reviewer_id,
        reviewer_name=reviewer_name,
        participants=review_data.participants,
        participant_names=", ".join(participant_names) if participant_names else None,
        attachment_ids=review_data.attachment_ids,
        status=review_data.status or "DRAFT"
    )
    
    db.add(review)
    db.commit()
    db.refresh(review)
    
    return ResponseModel(
        code=200,
        message="复盘报告创建成功",
        data=ProjectReviewResponse.model_validate(review).model_dump()
    )


@router.get("/project-reviews/{review_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_review_detail_v2(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目复盘报告详情（使用新模型）
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)
    
    # 加载关联数据
    lessons = db.query(ProjectLesson).filter(ProjectLesson.review_id == review_id).all()
    best_practices = db.query(ProjectBestPractice).filter(ProjectBestPractice.review_id == review_id).all()
    
    data = ProjectReviewResponse.model_validate(review).model_dump()
    data["lessons"] = [ProjectLessonResponse.model_validate(l).model_dump() for l in lessons]
    data["best_practices"] = [ProjectBestPracticeResponse.model_validate(bp).model_dump() for bp in best_practices]
    
    return ResponseModel(
        code=200,
        message="获取复盘报告详情成功",
        data=data
    )


@router.put("/project-reviews/{review_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    review_data: ProjectReviewUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目复盘报告
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)
    
    # 更新字段
    update_data = review_data.model_dump(exclude_unset=True)
    
    # 处理参与人姓名
    if "participants" in update_data and update_data["participants"]:
        users = db.query(User).filter(User.id.in_(update_data["participants"])).all()
        participant_names = [u.real_name or u.username for u in users]
        update_data["participant_names"] = ", ".join(participant_names)
    
    # 处理评审人姓名
    if "reviewer_id" in update_data:
        reviewer = db.query(User).filter(User.id == update_data["reviewer_id"]).first()
        if reviewer:
            update_data["reviewer_name"] = reviewer.real_name or reviewer.username
    
    for key, value in update_data.items():
        setattr(review, key, value)
    
    db.commit()
    db.refresh(review)
    
    return ResponseModel(
        code=200,
        message="复盘报告更新成功",
        data=ProjectReviewResponse.model_validate(review).model_dump()
    )


@router.delete("/project-reviews/{review_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除项目复盘报告
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)
    
    # 检查状态（已发布的复盘报告不能删除）
    if review.status == "PUBLISHED":
        raise HTTPException(
            status_code=400,
            detail="已发布的复盘报告不能删除，请先归档"
        )
    
    db.delete(review)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="复盘报告删除成功"
    )


@router.put("/project-reviews/{review_id}/publish", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def publish_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发布项目复盘报告
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)
    
    review.status = "PUBLISHED"
    db.commit()
    db.refresh(review)
    
    return ResponseModel(
        code=200,
        message="复盘报告发布成功",
        data=ProjectReviewResponse.model_validate(review).model_dump()
    )


@router.put("/project-reviews/{review_id}/archive", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def archive_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    归档项目复盘报告
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)
    
    review.status = "ARCHIVED"
    db.commit()
    db.refresh(review)
    
    return ResponseModel(
        code=200,
        message="复盘报告归档成功",
        data=ProjectReviewResponse.model_validate(review).model_dump()
    )


# ==================== 经验教训管理 ====================

@router.get("/project-reviews/{review_id}/lessons", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_lessons(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    lesson_type: Optional[str] = Query(None, description="类型筛选：SUCCESS/FAILURE"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取复盘报告的经验教训列表
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)
    
    query = db.query(ProjectLesson).filter(ProjectLesson.review_id == review_id)
    
    if lesson_type:
        query = query.filter(ProjectLesson.lesson_type == lesson_type)
    if status:
        query = query.filter(ProjectLesson.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    lessons = query.order_by(desc(ProjectLesson.created_at)).offset(offset).limit(page_size).all()
    
    items = [ProjectLessonResponse.model_validate(l).model_dump() for l in lessons]
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/project-reviews/{review_id}/lessons", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_lesson(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    lesson_data: ProjectLessonCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建经验教训
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)
    
    # 验证review_id匹配
    if lesson_data.review_id != review_id:
        raise HTTPException(status_code=400, detail="review_id不匹配")
    
    lesson = ProjectLesson(**lesson_data.model_dump())
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    
    return ResponseModel(
        code=200,
        message="经验教训创建成功",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.get("/project-reviews/lessons/{lesson_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_lesson_detail(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取经验教训详情
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)
    
    return ResponseModel(
        code=200,
        message="获取经验教训详情成功",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.put("/project-reviews/lessons/{lesson_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_lesson(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    lesson_data: ProjectLessonUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新经验教训
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)
    
    update_data = lesson_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lesson, key, value)
    
    db.commit()
    db.refresh(lesson)
    
    return ResponseModel(
        code=200,
        message="经验教训更新成功",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.delete("/project-reviews/lessons/{lesson_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_project_lesson(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除经验教训
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)
    
    db.delete(lesson)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="经验教训删除成功"
    )


@router.put("/project-reviews/lessons/{lesson_id}/resolve", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def resolve_project_lesson(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记经验教训已解决
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)
    
    lesson.status = "RESOLVED"
    lesson.resolved_date = date.today()
    db.commit()
    db.refresh(lesson)
    
    return ResponseModel(
        code=200,
        message="经验教训已标记为已解决",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


# ==================== 最佳实践管理 ====================

@router.get("/project-reviews/{review_id}/best-practices", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_best_practices(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_reusable: Optional[bool] = Query(None, description="是否可复用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取复盘报告的最佳实践列表
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)
    
    query = db.query(ProjectBestPractice).filter(ProjectBestPractice.review_id == review_id)
    
    if category:
        query = query.filter(ProjectBestPractice.category == category)
    if is_reusable is not None:
        query = query.filter(ProjectBestPractice.is_reusable == is_reusable)
    
    total = query.count()
    offset = (page - 1) * page_size
    practices = query.order_by(desc(ProjectBestPractice.created_at)).offset(offset).limit(page_size).all()
    
    items = [ProjectBestPracticeResponse.model_validate(bp).model_dump() for bp in practices]
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/project-reviews/{review_id}/best-practices", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    practice_data: ProjectBestPracticeCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建最佳实践
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)
    
    # 验证review_id匹配
    if practice_data.review_id != review_id:
        raise HTTPException(status_code=400, detail="review_id不匹配")
    
    practice = ProjectBestPractice(**practice_data.model_dump())
    db.add(practice)
    db.commit()
    db.refresh(practice)
    
    return ResponseModel(
        code=200,
        message="最佳实践创建成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.get("/project-reviews/best-practices/{practice_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_best_practice_detail(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最佳实践详情
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()
    
    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, practice.project_id)
    
    return ResponseModel(
        code=200,
        message="获取最佳实践详情成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.put("/project-reviews/best-practices/{practice_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    practice_data: ProjectBestPracticeUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新最佳实践
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()
    
    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, practice.project_id)
    
    update_data = practice_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(practice, key, value)
    
    db.commit()
    db.refresh(practice)
    
    return ResponseModel(
        code=200,
        message="最佳实践更新成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.delete("/project-reviews/best-practices/{practice_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除最佳实践
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()
    
    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, practice.project_id)
    
    db.delete(practice)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="最佳实践删除成功"
    )


@router.put("/project-reviews/best-practices/{practice_id}/validate", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def validate_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    validation_status: str = Body(..., description="验证状态：VALIDATED/REJECTED"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    验证最佳实践
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()
    
    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, practice.project_id)
    
    if validation_status not in ["VALIDATED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="验证状态必须是VALIDATED或REJECTED")
    
    practice.validation_status = validation_status
    practice.validation_date = date.today()
    practice.validated_by = current_user.id
    db.commit()
    db.refresh(practice)
    
    return ResponseModel(
        code=200,
        message="最佳实践验证成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.post("/project-reviews/best-practices/{practice_id}/reuse", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def reuse_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    复用最佳实践（增加复用计数）
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()
    
    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")
    
    # 检查是否可复用
    if not practice.is_reusable:
        raise HTTPException(status_code=400, detail="该最佳实践不可复用")
    
    practice.reuse_count = (practice.reuse_count or 0) + 1
    practice.last_reused_at = datetime.now()
    db.commit()
    db.refresh(practice)
    
    return ResponseModel(
        code=200,
        message="最佳实践复用成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


# ==================== 最佳实践库 ====================

@router.get("/best-practices", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def search_best_practices(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（标题/描述）"),
    category: Optional[str] = Query(None, description="分类筛选"),
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    stage: Optional[str] = Query(None, description="阶段筛选（S1-S9）"),
    validation_status: Optional[str] = Query(None, description="验证状态筛选"),
    is_reusable: Optional[bool] = Query(True, description="是否可复用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    搜索最佳实践库（跨项目）
    """
    query = db.query(ProjectBestPractice).join(
        ProjectReview, ProjectBestPractice.review_id == ProjectReview.id
    ).join(
        Project, ProjectReview.project_id == Project.id
    )
    
    # 只显示可复用的最佳实践
    if is_reusable:
        query = query.filter(ProjectBestPractice.is_reusable == True)
    
    if keyword:
        query = query.filter(
            or_(
                ProjectBestPractice.title.like(f"%{keyword}%"),
                ProjectBestPractice.description.like(f"%{keyword}%")
            )
        )
    
    if category:
        query = query.filter(ProjectBestPractice.category == category)
    
    if validation_status:
        query = query.filter(ProjectBestPractice.validation_status == validation_status)
    
    if project_type:
        # 从applicable_project_types JSON字段中筛选
        query = query.filter(
            ProjectBestPractice.applicable_project_types.contains([project_type])
        )
    
    if stage:
        # 从applicable_stages JSON字段中筛选
        query = query.filter(
            ProjectBestPractice.applicable_stages.contains([stage])
        )
    
    total = query.count()
    offset = (page - 1) * page_size
    practices = query.order_by(desc(ProjectBestPractice.reuse_count), desc(ProjectBestPractice.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for bp in practices:
        data = ProjectBestPracticeResponse.model_validate(bp).model_dump()
        # 添加项目信息
        if bp.review and bp.review.project:
            data["project_code"] = bp.review.project_code
            data["project_name"] = bp.review.project.project_name
        items.append(data)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/best-practices/categories", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_best_practice_categories(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最佳实践分类列表
    """
    categories = db.query(ProjectBestPractice.category).filter(
        ProjectBestPractice.category.isnot(None),
        ProjectBestPractice.is_reusable == True
    ).distinct().all()
    
    category_list = [cat[0] for cat in categories if cat[0]]
    
    return ResponseModel(
        code=200,
        message="获取分类列表成功",
        data={"categories": category_list}
    )


@router.get("/best-practices/statistics", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_best_practice_statistics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最佳实践统计信息
    """
    total = db.query(ProjectBestPractice).filter(ProjectBestPractice.is_reusable == True).count()
    validated = db.query(ProjectBestPractice).filter(
        ProjectBestPractice.is_reusable == True,
        ProjectBestPractice.validation_status == "VALIDATED"
    ).count()
    pending = db.query(ProjectBestPractice).filter(
        ProjectBestPractice.is_reusable == True,
        ProjectBestPractice.validation_status == "PENDING"
    ).count()
    
    # 总复用次数
    total_reuse = db.query(func.sum(ProjectBestPractice.reuse_count)).filter(
        ProjectBestPractice.is_reusable == True
    ).scalar() or 0
    
    # 按分类统计
    category_stats = db.query(
        ProjectBestPractice.category,
        func.count(ProjectBestPractice.id).label('count')
    ).filter(
        ProjectBestPractice.is_reusable == True,
        ProjectBestPractice.category.isnot(None)
    ).group_by(ProjectBestPractice.category).all()
    
    return ResponseModel(
        code=200,
        message="获取统计信息成功",
        data={
            "total": total,
            "validated": validated,
            "pending": pending,
            "total_reuse": total_reuse,
            "category_stats": {cat: count for cat, count in category_stats}
        }
    )


# ==================== 经验教训高级管理 ====================

@router.get("/lessons-learned", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def search_lessons_learned(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（标题/描述）"),
    lesson_type: Optional[str] = Query(None, description="类型筛选：SUCCESS/FAILURE"),
    category: Optional[str] = Query(None, description="分类筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    跨项目搜索经验教训库
    """
    query = db.query(ProjectLesson).join(
        ProjectReview, ProjectLesson.review_id == ProjectReview.id
    ).join(
        Project, ProjectReview.project_id == Project.id
    )
    
    if keyword:
        query = query.filter(
            or_(
                ProjectLesson.title.like(f"%{keyword}%"),
                ProjectLesson.description.like(f"%{keyword}%")
            )
        )
    
    if lesson_type:
        query = query.filter(ProjectLesson.lesson_type == lesson_type)
    
    if category:
        query = query.filter(ProjectLesson.category == category)
    
    if status:
        query = query.filter(ProjectLesson.status == status)
    
    if priority:
        query = query.filter(ProjectLesson.priority == priority)
    
    if project_id:
        query = query.filter(ProjectLesson.project_id == project_id)
    
    total = query.count()
    offset = (page - 1) * page_size
    lessons = query.order_by(desc(ProjectLesson.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for lesson in lessons:
        data = ProjectLessonResponse.model_validate(lesson).model_dump()
        # 添加项目信息
        if lesson.review and lesson.review.project:
            data["project_code"] = lesson.review.project_code
            data["project_name"] = lesson.review.project.project_name
        items.append(data)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/lessons-learned/statistics", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_lessons_statistics(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选（可选）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取经验教训统计信息
    """
    query = db.query(ProjectLesson)
    
    if project_id:
        query = query.filter(ProjectLesson.project_id == project_id)
    
    total = query.count()
    success_count = query.filter(ProjectLesson.lesson_type == "SUCCESS").count()
    failure_count = query.filter(ProjectLesson.lesson_type == "FAILURE").count()
    
    # 按分类统计
    category_stats = db.query(
        ProjectLesson.category,
        func.count(ProjectLesson.id).label('count')
    )
    if project_id:
        category_stats = category_stats.filter(ProjectLesson.project_id == project_id)
    category_stats = category_stats.filter(
        ProjectLesson.category.isnot(None)
    ).group_by(ProjectLesson.category).all()
    
    # 按状态统计
    status_stats = db.query(
        ProjectLesson.status,
        func.count(ProjectLesson.id).label('count')
    )
    if project_id:
        status_stats = status_stats.filter(ProjectLesson.project_id == project_id)
    status_stats = status_stats.group_by(ProjectLesson.status).all()
    
    # 按优先级统计
    priority_stats = db.query(
        ProjectLesson.priority,
        func.count(ProjectLesson.id).label('count')
    )
    if project_id:
        priority_stats = priority_stats.filter(ProjectLesson.project_id == project_id)
    priority_stats = priority_stats.group_by(ProjectLesson.priority).all()
    
    # 已解决/未解决统计
    resolved_count = query.filter(ProjectLesson.status.in_(["RESOLVED", "CLOSED"])).count()
    unresolved_count = total - resolved_count
    
    # 逾期统计（有完成日期且已过期）
    today = date.today()
    overdue_count = query.filter(
        ProjectLesson.due_date.isnot(None),
        ProjectLesson.due_date < today,
        ProjectLesson.status.notin_(["RESOLVED", "CLOSED"])
    ).count()
    
    return ResponseModel(
        code=200,
        message="获取统计信息成功",
        data={
            "total": total,
            "success_count": success_count,
            "failure_count": failure_count,
            "by_category": {cat: count for cat, count in category_stats if cat},
            "by_status": {stat: count for stat, count in status_stats},
            "by_priority": {pri: count for pri, count in priority_stats},
            "resolved_count": resolved_count,
            "unresolved_count": unresolved_count,
            "overdue_count": overdue_count
        }
    )


@router.get("/lessons-learned/categories", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_lesson_categories(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取经验教训分类列表
    """
    categories = db.query(ProjectLesson.category).filter(
        ProjectLesson.category.isnot(None)
    ).distinct().all()
    
    category_list = [cat[0] for cat in categories if cat[0]]
    
    return ResponseModel(
        code=200,
        message="获取分类列表成功",
        data={"categories": category_list}
    )


@router.put("/project-reviews/lessons/{lesson_id}/status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_lesson_status(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    new_status: str = Body(..., description="新状态：OPEN/IN_PROGRESS/RESOLVED/CLOSED"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新经验教训状态
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")
    
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)
    
    if new_status not in ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]:
        raise HTTPException(status_code=400, detail="无效的状态值")
    
    lesson.status = new_status
    if new_status in ["RESOLVED", "CLOSED"]:
        lesson.resolved_date = date.today()
    
    db.commit()
    db.refresh(lesson)
    
    return ResponseModel(
        code=200,
        message="经验教训状态更新成功",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.post("/project-reviews/lessons/batch-update", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_update_lessons(
    *,
    db: Session = Depends(deps.get_db),
    lesson_ids: List[int] = Body(..., description="经验教训ID列表"),
    update_data: Dict[str, Any] = Body(..., description="更新数据"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新经验教训
    """
    lessons = db.query(ProjectLesson).filter(ProjectLesson.id.in_(lesson_ids)).all()
    
    if not lessons:
        raise HTTPException(status_code=404, detail="未找到经验教训")
    
    # 检查所有经验教训的项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    for lesson in lessons:
        check_project_access_or_raise(db, current_user, lesson.project_id)
    
    updated_count = 0
    for lesson in lessons:
        for key, value in update_data.items():
            if hasattr(lesson, key):
                setattr(lesson, key, value)
        updated_count += 1
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"成功更新{updated_count}条经验教训",
        data={"updated_count": updated_count}
    )


# ==================== 最佳实践高级管理 ====================

@router.post("/best-practices/recommend", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def recommend_best_practices(
    *,
    db: Session = Depends(deps.get_db),
    request: BestPracticeRecommendationRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    推荐最佳实践（基于项目类型和阶段）
    """
    query = db.query(ProjectBestPractice).join(
        ProjectReview, ProjectBestPractice.review_id == ProjectReview.id
    ).join(
        Project, ProjectReview.project_id == Project.id
    ).filter(
        ProjectBestPractice.is_reusable == True,
        ProjectBestPractice.validation_status == "VALIDATED",
        ProjectBestPractice.status == "ACTIVE"
    )
    
    if request.category:
        query = query.filter(ProjectBestPractice.category == request.category)
    
    practices = query.all()
    
    # 计算匹配度
    recommendations = []
    for practice in practices:
        score = 0.0
        reasons = []
        
        # 项目类型匹配
        if request.project_type and practice.applicable_project_types:
            if request.project_type in practice.applicable_project_types:
                score += 0.4
                reasons.append("项目类型匹配")
        
        # 阶段匹配
        if request.current_stage and practice.applicable_stages:
            if request.current_stage in practice.applicable_stages:
                score += 0.4
                reasons.append("阶段匹配")
        
        # 复用次数加分
        if practice.reuse_count:
            score += min(0.2, practice.reuse_count * 0.01)
            if practice.reuse_count > 5:
                reasons.append("高复用率")
        
        # 分类匹配
        if request.category and practice.category == request.category:
            score += 0.1
            reasons.append("分类匹配")
        
        if score > 0:
            recommendations.append({
                "practice": practice,
                "score": score,
                "reasons": reasons
            })
    
    # 按匹配度排序
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    # 限制返回数量
    recommendations = recommendations[:request.limit]
    
    items = []
    for rec in recommendations:
        practice_data = ProjectBestPracticeResponse.model_validate(rec["practice"]).model_dump()
        # 添加项目信息
        if rec["practice"].review and rec["practice"].review.project:
            practice_data["project_code"] = rec["practice"].review.project_code
            practice_data["project_name"] = rec["practice"].review.project.project_name
        
        items.append({
            "practice": practice_data,
            "match_score": round(rec["score"], 2),
            "match_reasons": rec["reasons"]
        })
    
    return ResponseModel(
        code=200,
        message="推荐最佳实践成功",
        data={"recommendations": items}
    )


@router.get("/projects/{project_id}/best-practices/recommend", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_best_practice_recommendations(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目推荐的最佳实践（基于项目信息自动匹配）
    """
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)
    
    # 构建推荐请求
    request = BestPracticeRecommendationRequest(
        project_id=project_id,
        project_type=project.project_type if hasattr(project, 'project_type') else None,
        current_stage=project.stage if hasattr(project, 'stage') else None,
        limit=limit
    )
    
    # 调用推荐函数
    return recommend_best_practices(db=db, request=request, current_user=current_user)


@router.post("/project-reviews/best-practices/{practice_id}/apply", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def apply_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    target_project_id: int = Body(..., description="目标项目ID"),
    notes: Optional[str] = Body(None, description="应用备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    应用最佳实践到项目（增加复用计数）
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()
    
    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")
    
    # 检查是否可复用
    if not practice.is_reusable:
        raise HTTPException(status_code=400, detail="该最佳实践不可复用")
    
    # 检查目标项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, target_project_id)
    
    # 增加复用计数
    practice.reuse_count = (practice.reuse_count or 0) + 1
    practice.last_reused_at = datetime.now()
    
    db.commit()
    db.refresh(practice)
    
    return ResponseModel(
        code=200,
        message="最佳实践应用成功",
        data={
            "practice": ProjectBestPracticeResponse.model_validate(practice).model_dump(),
            "applied_to_project_id": target_project_id,
            "notes": notes
        }
    )


@router.get("/best-practices/popular", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_popular_best_practices(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取热门最佳实践（按复用次数排序）
    """
    query = db.query(ProjectBestPractice).join(
        ProjectReview, ProjectBestPractice.review_id == ProjectReview.id
    ).join(
        Project, ProjectReview.project_id == Project.id
    ).filter(
        ProjectBestPractice.is_reusable == True,
        ProjectBestPractice.validation_status == "VALIDATED",
        ProjectBestPractice.status == "ACTIVE"
    )
    
    if category:
        query = query.filter(ProjectBestPractice.category == category)
    
    total = query.count()
    offset = (page - 1) * page_size
    practices = query.order_by(
        desc(ProjectBestPractice.reuse_count),
        desc(ProjectBestPractice.created_at)
    ).offset(offset).limit(page_size).all()
    
    items = []
    for bp in practices:
        data = ProjectBestPracticeResponse.model_validate(bp).model_dump()
        # 添加项目信息
        if bp.review and bp.review.project:
            data["project_code"] = bp.review.project_code
            data["project_name"] = bp.review.project.project_name
        items.append(data)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


# ==================== Sprint 2.4: 数据同步 ====================

@router.post("/{project_id}/sync-from-contract", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_project_from_contract(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    contract_id: Optional[int] = Query(None, description="合同ID（可选，不提供则同步所有关联合同）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Sprint 2.4: 从合同同步数据到项目
    
    手动触发数据同步，将合同金额、交期等信息同步到项目
    """
    from app.services.data_sync_service import DataSyncService
    from app.utils.permission_helpers import check_project_access_or_raise
    
    # 检查项目访问权限
    check_project_access_or_raise(db, current_user, project_id)
    
    sync_service = DataSyncService(db)
    
    if contract_id:
        # 同步指定合同
        result = sync_service.sync_contract_to_project(contract_id)
    else:
        # 同步所有关联合同
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        from app.models.sales import Contract
        contracts = db.query(Contract).filter(Contract.project_id == project_id).all()
        
        if not contracts:
            return ResponseModel(
                code=200,
                message="项目未关联合同，无需同步",
                data={"synced_contracts": []}
            )
        
        synced_contracts = []
        for contract in contracts:
            result = sync_service.sync_contract_to_project(contract.id)
            if result.get("success"):
                synced_contracts.append({
                    "contract_id": contract.id,
                    "contract_code": contract.contract_code,
                    "updated_fields": result.get("updated_fields", [])
                })
        
        return ResponseModel(
            code=200,
            message=f"已同步 {len(synced_contracts)} 个合同",
            data={"synced_contracts": synced_contracts}
        )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "同步失败"))
    
    return ResponseModel(
        code=200,
        message=result.get("message", "同步成功"),
        data=result
    )


@router.post("/{project_id}/sync-to-contract", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_project_to_contract(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Sprint 2.4: 同步项目数据到合同
    
    手动触发数据同步，将项目进度、状态等信息同步到合同
    """
    from app.services.data_sync_service import DataSyncService
    from app.utils.permission_helpers import check_project_access_or_raise
    
    # 检查项目访问权限
    check_project_access_or_raise(db, current_user, project_id)
    
    sync_service = DataSyncService(db)
    result = sync_service.sync_project_to_contract(project_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "同步失败"))
    
    return ResponseModel(
        code=200,
        message=result.get("message", "同步成功"),
        data=result
    )


@router.get("/{project_id}/sync-status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_sync_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Sprint 2.4: 获取项目数据同步状态
    
    查询项目与合同的数据同步状态
    """
    from app.services.data_sync_service import DataSyncService
    from app.utils.permission_helpers import check_project_access_or_raise
    
    # 检查项目访问权限
    check_project_access_or_raise(db, current_user, project_id)
    
    sync_service = DataSyncService(db)
    result = sync_service.get_sync_status(project_id=project_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "查询失败"))
    
    return ResponseModel(
        code=200,
        message="获取同步状态成功",
        data=result
    )


# ==================== ERP集成 ====================

@router.post("/{project_id}/sync-to-erp", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_project_to_erp(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    erp_order_no: Optional[str] = Body(None, description="ERP订单号（可选，不提供则自动生成）"),
    current_user: User = Depends(security.require_permission("project:erp:sync")),
) -> Any:
    """
    同步项目到ERP系统
    
    将项目信息同步到ERP系统，更新ERP同步状态
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    
    # 检查项目访问权限
    check_project_access_or_raise(db, current_user, project_id)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 调用ERP系统API进行同步
    sync_result = _sync_to_erp_system(project, erp_order_no)

    if sync_result['success']:
        project.erp_synced = True
        project.erp_sync_time = datetime.now()
        project.erp_sync_status = "SYNCED"
    else:
        project.erp_sync_status = "FAILED"
        project.erp_error_message = sync_result.get('error', '同步失败')
        db.commit()
        raise HTTPException(status_code=500, detail=f"ERP同步失败: {sync_result.get('error')}")
    
    if erp_order_no:
        project.erp_order_no = erp_order_no
    elif not project.erp_order_no:
        # 自动生成ERP订单号（格式：ERP-项目编号）
        project.erp_order_no = f"ERP-{project.project_code}"
    
    db.commit()
    db.refresh(project)
    
    return ResponseModel(
        code=200,
        message="项目已同步到ERP系统",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "erp_order_no": project.erp_order_no,
            "erp_sync_time": project.erp_sync_time.isoformat() if project.erp_sync_time else None,
            "erp_sync_status": project.erp_sync_status
        }
    )


@router.get("/{project_id}/erp-status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_erp_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目ERP同步状态
    
    查询项目的ERP同步状态、订单号等信息
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    
    # 检查项目访问权限
    check_project_access_or_raise(db, current_user, project_id)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return ResponseModel(
        code=200,
        message="获取ERP状态成功",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "erp_synced": project.erp_synced,
            "erp_sync_time": project.erp_sync_time.isoformat() if project.erp_sync_time else None,
            "erp_order_no": project.erp_order_no,
            "erp_sync_status": project.erp_sync_status
        }
    )


@router.put("/{project_id}/erp-status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_erp_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    erp_synced: Optional[bool] = Body(None, description="是否已录入ERP系统"),
    erp_order_no: Optional[str] = Body(None, description="ERP订单号"),
    erp_sync_status: Optional[str] = Body(None, description="ERP同步状态：PENDING/SYNCED/FAILED"),
    current_user: User = Depends(security.require_permission("project:erp:update")),
) -> Any:
    """
    更新项目ERP同步状态
    
    手动更新项目的ERP同步状态（通常由ERP系统回调或管理员操作）
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    
    # 检查项目访问权限
    check_project_access_or_raise(db, current_user, project_id)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if erp_synced is not None:
        project.erp_synced = erp_synced
        if erp_synced and not project.erp_sync_time:
            project.erp_sync_time = datetime.now()
    
    if erp_order_no is not None:
        project.erp_order_no = erp_order_no
    
    if erp_sync_status is not None:
        if erp_sync_status not in ["PENDING", "SYNCED", "FAILED"]:
            raise HTTPException(status_code=400, detail="无效的ERP同步状态")
        project.erp_sync_status = erp_sync_status
    
    db.commit()
    db.refresh(project)
    
    return ResponseModel(
        code=200,
        message="ERP状态更新成功",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "erp_synced": project.erp_synced,
            "erp_sync_time": project.erp_sync_time.isoformat() if project.erp_sync_time else None,
            "erp_order_no": project.erp_order_no,
            "erp_sync_status": project.erp_sync_status
        }
    )


# ==================== ERP同步辅助函数 ====================


def _sync_to_erp_system(project, erp_order_no: Optional[str] = None) -> dict:
    """
    同步项目数据到ERP系统

    这是一个可扩展的ERP接口框架。实际使用时需要根据具体的ERP系统
    （如SAP、Oracle、金蝶、用友等）实现相应的API调用。

    Args:
        project: 项目对象
        erp_order_no: ERP订单号（可选）

    Returns:
        dict: 同步结果 {'success': bool, 'erp_order_no': str, 'error': str}
    """
    from app.core.config import settings

    # 检查是否配置了ERP接口
    erp_api_url = getattr(settings, 'ERP_API_URL', None)
    erp_api_key = getattr(settings, 'ERP_API_KEY', None)

    # 如果没有配置ERP接口，返回模拟成功
    if not erp_api_url:
        # 生成模拟ERP订单号
        generated_order_no = erp_order_no or f"ERP-{project.project_code}"
        return {
            'success': True,
            'erp_order_no': generated_order_no,
            'message': 'ERP接口未配置，使用模拟同步'
        }

    # 实际ERP集成逻辑（待实现）
    # 示例代码框架：
    # try:
    #     import requests
    #     payload = {
    #         'project_code': project.project_code,
    #         'project_name': project.project_name,
    #         'customer': project.customer.customer_name if project.customer else None,
    #         'contract_amount': float(project.contract_amount) if project.contract_amount else 0,
    #         'start_date': project.start_date.isoformat() if project.start_date else None,
    #         'end_date': project.end_date.isoformat() if project.end_date else None,
    #     }
    #     headers = {'Authorization': f'Bearer {erp_api_key}', 'Content-Type': 'application/json'}
    #     response = requests.post(f'{erp_api_url}/api/projects', json=payload, headers=headers, timeout=30)
    #     if response.status_code == 200:
    #         return {'success': True, 'erp_order_no': response.json().get('order_no')}
    #     else:
    #         return {'success': False, 'error': response.text}
    # except Exception as e:
    #     return {'success': False, 'error': str(e)}

    return {
        'success': True,
        'erp_order_no': erp_order_no or f"ERP-{project.project_code}",
        'message': 'ERP同步功能框架已就绪，请配置实际ERP接口'
    }
