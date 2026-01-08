from typing import Any, List, Optional, Tuple, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project, Customer, ProjectStatusLog, ProjectPaymentPlan, ProjectMilestone, ProjectTemplate, ProjectTemplateVersion, Machine, ProjectStage, ProjectMember
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
    ProjectStatusResponse,
    BatchUpdateStatusRequest,
    BatchArchiveRequest,
    BatchAssignPMRequest,
    BatchUpdateStageRequest,
    BatchOperationResponse,
    ProjectDashboardResponse,
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

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Project.project_name.contains(keyword),
                Project.project_code.contains(keyword),
                Project.contract_no.contains(keyword),
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

    # 总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    projects = query.order_by(desc(Project.created_at)).offset(offset).limit(page_size).all()

    return PaginatedResponse(
        items=projects,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


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
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目详情（包含关联数据）
    """
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)
    
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

    return project


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
    # 应用数据权限过滤
    from app.services.data_scope_service import DataScopeService
    query = db.query(Project).filter(Project.is_active == True)
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    
    # 按状态统计
    status_query = query
    status_stats = (
        status_query.with_entities(Project.status, func.count(Project.id).label('count'))
        .group_by(Project.status)
        .all()
    )
    
    # 按阶段统计
    stage_query = query
    stage_stats = (
        stage_query.with_entities(Project.stage, func.count(Project.id).label('count'))
        .group_by(Project.stage)
        .all()
    )
    
    # 按健康度统计
    health_query = query
    health_stats = (
        health_query.with_entities(Project.health, func.count(Project.id).label('count'))
        .group_by(Project.health)
        .all()
    )
    
    # 总体统计
    total_projects = query.count()
    avg_progress = query.with_entities(func.avg(Project.progress_pct)).scalar() or 0
    
    # 按项目经理统计
    pm_query = query.filter(Project.pm_id.isnot(None))
    pm_stats = (
        pm_query.with_entities(Project.pm_id, Project.pm_name, func.count(Project.id).label('count'))
        .group_by(Project.pm_id, Project.pm_name)
        .all()
    )
    
    stats_data = {
        "total": total_projects,
        "average_progress": float(avg_progress),
        "by_status": {status: count for status, count in status_stats if status},
        "by_stage": {stage: count for stage, count in stage_stats if stage},
        "by_health": {health: count for health, count in health_stats if health},
        "by_pm": [
            {
                "pm_id": pm_id,
                "pm_name": pm_name or "未分配",
                "count": count
            }
            for pm_id, pm_name, count in pm_stats
        ],
    }
    
    # 按客户统计
    if group_by == "customer":
        customer_query = query.filter(Project.customer_id.isnot(None))
        customer_stats = (
            customer_query.with_entities(
                Project.customer_id,
                Project.customer_name,
                func.count(Project.id).label('count'),
                func.sum(Project.contract_amount).label('total_amount')
            )
            .group_by(Project.customer_id, Project.customer_name)
            .all()
        )
        
        stats_data["by_customer"] = [
            {
                "customer_id": customer_id,
                "customer_name": customer_name or "未知客户",
                "count": count,
                "total_amount": float(total_amount or 0),
            }
            for customer_id, customer_name, count, total_amount in customer_stats
        ]
    
    # 按月份统计
    if group_by == "month":
        # 如果没有指定日期范围，默认统计最近12个月
        if not start_date or not end_date:
            today = date.today()
            end_date = today
            start_date = date(today.year - 1, today.month, 1)
        
        # 按项目创建月份统计
        month_query = query.filter(
            Project.created_at >= datetime.combine(start_date, datetime.min.time()),
            Project.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        
        # 使用SQLite的strftime或MySQL的DATE_FORMAT
        from sqlalchemy import case, extract
        try:
            # 尝试使用extract（适用于大多数数据库）
            month_stats = (
                month_query.with_entities(
                    extract('year', Project.created_at).label('year'),
                    extract('month', Project.created_at).label('month'),
                    func.count(Project.id).label('count'),
                    func.sum(Project.contract_amount).label('total_amount')
                )
                .group_by(
                    extract('year', Project.created_at),
                    extract('month', Project.created_at)
                )
                .order_by(
                    extract('year', Project.created_at),
                    extract('month', Project.created_at)
                )
                .all()
            )
        except:
            # 如果extract不支持，使用字符串格式化（SQLite）
            month_stats = (
                month_query.with_entities(
                    func.strftime('%Y', Project.created_at).label('year'),
                    func.strftime('%m', Project.created_at).label('month'),
                    func.count(Project.id).label('count'),
                    func.sum(Project.contract_amount).label('total_amount')
                )
                .group_by(
                    func.strftime('%Y', Project.created_at),
                    func.strftime('%m', Project.created_at)
                )
                .order_by(
                    func.strftime('%Y', Project.created_at),
                    func.strftime('%m', Project.created_at)
                )
                .all()
            )
        
        stats_data["by_month"] = [
            {
                "year": int(year),
                "month": int(month),
                "month_label": f"{int(year)}-{int(month):02d}",
                "count": count,
                "total_amount": float(total_amount or 0),
            }
            for year, month, count, total_amount in month_stats
        ]
    
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
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
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
    
    # 补充变更人姓名
    result = []
    for log in logs:
        log_dict = {
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
        result.append(log_dict)
    
    return result


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
    
    db.add(project)
    
    # 更新模板使用次数
    template.usage_count += 1
    
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
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    relations = []
    
    # 1. 物料转移关联
    if not relation_type or relation_type == 'MATERIAL_TRANSFER':
        outbound_transfers = db.query(MaterialTransfer).filter(
            MaterialTransfer.from_project_id == project_id,
            MaterialTransfer.status.in_(['APPROVED', 'EXECUTED'])
        ).all()
        
        for transfer in outbound_transfers:
            if transfer.to_project_id:
                to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
                if to_project:
                    relations.append({
                        'type': 'MATERIAL_TRANSFER_OUT',
                        'related_project_id': transfer.to_project_id,
                        'related_project_code': to_project.project_code,
                        'related_project_name': to_project.project_name,
                        'relation_detail': {
                            'transfer_no': transfer.transfer_no,
                            'material_code': transfer.material_code,
                            'material_name': transfer.material_name,
                            'transfer_qty': float(transfer.transfer_qty),
                        },
                        'strength': 'MEDIUM',
                    })
        
        inbound_transfers = db.query(MaterialTransfer).filter(
            MaterialTransfer.to_project_id == project_id,
            MaterialTransfer.status.in_(['APPROVED', 'EXECUTED'])
        ).all()
        
        for transfer in inbound_transfers:
            if transfer.from_project_id:
                from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first()
                if from_project:
                    relations.append({
                        'type': 'MATERIAL_TRANSFER_IN',
                        'related_project_id': transfer.from_project_id,
                        'related_project_code': from_project.project_code,
                        'related_project_name': from_project.project_name,
                        'relation_detail': {
                            'transfer_no': transfer.transfer_no,
                            'material_code': transfer.material_code,
                            'material_name': transfer.material_name,
                            'transfer_qty': float(transfer.transfer_qty),
                        },
                        'strength': 'MEDIUM',
                    })
    
    # 2. 共享资源关联
    if not relation_type or relation_type == 'SHARED_RESOURCE':
        project_resources = db.query(PmoResourceAllocation).filter(
            PmoResourceAllocation.project_id == project_id,
            PmoResourceAllocation.status != 'CANCELLED'
        ).all()
        
        resource_ids = [alloc.resource_id for alloc in project_resources]
        
        if resource_ids:
            shared_resource_projects = (
                db.query(PmoResourceAllocation.project_id, func.count(PmoResourceAllocation.id).label('shared_count'))
                .filter(
                    PmoResourceAllocation.resource_id.in_(resource_ids),
                    PmoResourceAllocation.project_id != project_id,
                    PmoResourceAllocation.status != 'CANCELLED'
                )
                .group_by(PmoResourceAllocation.project_id)
                .all()
            )
            
            for shared_project_id, shared_count in shared_resource_projects:
                shared_project = db.query(Project).filter(Project.id == shared_project_id).first()
                if shared_project:
                    shared_resources = (
                        db.query(PmoResourceAllocation)
                        .filter(
                            PmoResourceAllocation.project_id == shared_project_id,
                            PmoResourceAllocation.resource_id.in_(resource_ids),
                            PmoResourceAllocation.status != 'CANCELLED'
                        )
                        .all()
                    )
                    
                    relations.append({
                        'type': 'SHARED_RESOURCE',
                        'related_project_id': shared_project_id,
                        'related_project_code': shared_project.project_code,
                        'related_project_name': shared_project.project_name,
                        'relation_detail': {
                            'shared_resource_count': shared_count,
                            'shared_resources': [
                                {
                                    'resource_id': r.resource_id,
                                    'resource_name': r.resource_name,
                                    'allocation_percent': r.allocation_percent,
                                }
                                for r in shared_resources
                            ],
                        },
                        'strength': 'HIGH' if shared_count >= 3 else 'MEDIUM',
                    })
    
    # 3. 共享客户关联
    if not relation_type or relation_type == 'SHARED_CUSTOMER':
        if project.customer_id:
            customer_projects = db.query(Project).filter(
                Project.customer_id == project.customer_id,
                Project.id != project_id,
                Project.is_active == True
            ).all()
            
            for customer_project in customer_projects:
                relations.append({
                    'type': 'SHARED_CUSTOMER',
                    'related_project_id': customer_project.id,
                    'related_project_code': customer_project.project_code,
                    'related_project_name': customer_project.project_name,
                    'relation_detail': {
                        'customer_id': project.customer_id,
                        'customer_name': project.customer_name,
                    },
                    'strength': 'LOW',
                })
    
    # 统计
    relation_stats = {
        'total_relations': len(relations),
        'by_type': {},
        'by_strength': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    }
    
    for relation in relations:
        rel_type = relation['type']
        strength = relation['strength']
        
        if rel_type not in relation_stats['by_type']:
            relation_stats['by_type'][rel_type] = 0
        relation_stats['by_type'][rel_type] += 1
        
        relation_stats['by_strength'][strength] += 1
    
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
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    discovered_relations = []
    
    # 1. 相同客户的项目（置信度：0.8）
    if project.customer_id:
        customer_projects = db.query(Project).filter(
            Project.customer_id == project.customer_id,
            Project.id != project_id,
            Project.is_active == True
        ).all()
        for related_project in customer_projects:
            discovered_relations.append({
                'related_project_id': related_project.id,
                'related_project_code': related_project.project_code,
                'related_project_name': related_project.project_name,
                'relation_type': 'SAME_CUSTOMER',
                'confidence': 0.8,
                'reason': f'相同客户：{project.customer_name}',
            })
    
    # 2. 相同项目经理的项目（置信度：0.7）
    if project.pm_id:
        pm_projects = db.query(Project).filter(
            Project.pm_id == project.pm_id,
            Project.id != project_id,
            Project.is_active == True
        ).all()
        for related_project in pm_projects:
            discovered_relations.append({
                'related_project_id': related_project.id,
                'related_project_code': related_project.project_code,
                'related_project_name': related_project.project_name,
                'relation_type': 'SAME_PM',
                'confidence': 0.7,
                'reason': f'相同项目经理：{project.pm_name}',
            })
    
    # 3. 时间重叠的项目（置信度：0.6）
    if project.planned_start_date and project.planned_end_date:
        overlapping_projects = db.query(Project).filter(
            Project.id != project_id,
            Project.is_active == True,
            Project.planned_start_date <= project.planned_end_date,
            Project.planned_end_date >= project.planned_start_date
        ).all()
        for related_project in overlapping_projects:
            discovered_relations.append({
                'related_project_id': related_project.id,
                'related_project_code': related_project.project_code,
                'related_project_name': related_project.project_name,
                'relation_type': 'TIME_OVERLAP',
                'confidence': 0.6,
                'reason': '项目时间重叠',
            })
    
    # 4. 物料转移记录（置信度：0.9）
    material_transfers = db.query(MaterialTransfer).filter(
        or_(
            MaterialTransfer.from_project_id == project_id,
            MaterialTransfer.to_project_id == project_id
        ),
        MaterialTransfer.status.in_(['APPROVED', 'EXECUTED'])
    ).all()
    for transfer in material_transfers:
        related_project_id = transfer.to_project_id if transfer.from_project_id == project_id else transfer.from_project_id
        if related_project_id:
            related_project = db.query(Project).filter(Project.id == related_project_id).first()
            if related_project:
                discovered_relations.append({
                    'related_project_id': related_project.id,
                    'related_project_code': related_project.project_code,
                    'related_project_name': related_project.project_name,
                    'relation_type': 'MATERIAL_TRANSFER',
                    'confidence': 0.9,
                    'reason': f'物料转移：{transfer.material_name}',
                })
    
    # 5. 共享资源（置信度：0.75）
    project_resources = db.query(PmoResourceAllocation).filter(
        PmoResourceAllocation.project_id == project_id,
        PmoResourceAllocation.status != 'CANCELLED'
    ).all()
    resource_ids = [alloc.resource_id for alloc in project_resources]
    if resource_ids:
        shared_projects = (
            db.query(PmoResourceAllocation.project_id)
            .filter(
                PmoResourceAllocation.resource_id.in_(resource_ids),
                PmoResourceAllocation.project_id != project_id,
                PmoResourceAllocation.status != 'CANCELLED'
            )
            .distinct()
            .all()
        )
        for (related_project_id,) in shared_projects:
            related_project = db.query(Project).filter(Project.id == related_project_id).first()
            if related_project:
                discovered_relations.append({
                    'related_project_id': related_project.id,
                    'related_project_code': related_project.project_code,
                    'related_project_name': related_project.project_name,
                    'relation_type': 'SHARED_RESOURCE',
                    'confidence': 0.75,
                    'reason': '共享资源',
                })
    
    # 6. 关联的研发项目（置信度：0.85）
    from app.models.rd_project import RdProject
    linked_rd_projects = db.query(RdProject).filter(
        RdProject.linked_project_id == project_id
    ).all()
    for rd_project in linked_rd_projects:
        # 查找其他关联到相同研发项目的非标项目
        other_linked_projects = db.query(RdProject).filter(
            RdProject.id == rd_project.id,
            RdProject.linked_project_id != project_id,
            RdProject.linked_project_id.isnot(None)
        ).all()
        for other_rd in other_linked_projects:
            if other_rd.linked_project_id:
                related_project = db.query(Project).filter(Project.id == other_rd.linked_project_id).first()
                if related_project:
                    discovered_relations.append({
                        'related_project_id': related_project.id,
                        'related_project_code': related_project.project_code,
                        'related_project_name': related_project.project_name,
                        'relation_type': 'SHARED_RD_PROJECT',
                        'confidence': 0.85,
                        'reason': f'关联相同研发项目：{rd_project.project_name}',
                    })
    
    # 去重并过滤置信度
    unique_relations = {}
    for relation in discovered_relations:
        if relation['confidence'] >= min_confidence:
            key = relation['related_project_id']
            if key not in unique_relations or relation['confidence'] > unique_relations[key]['confidence']:
                unique_relations[key] = relation
    
    # 按置信度排序
    final_relations = sorted(unique_relations.values(), key=lambda x: x['confidence'], reverse=True)
    
    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.project_name,
        'min_confidence': min_confidence,
        'total_discovered': len(final_relations),
        'relations': final_relations,
        'statistics': {
            'by_type': {},
            'by_confidence_range': {
                'high': len([r for r in final_relations if r['confidence'] >= 0.8]),
                'medium': len([r for r in final_relations if 0.5 <= r['confidence'] < 0.8]),
                'low': len([r for r in final_relations if r['confidence'] < 0.5]),
            }
        }
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
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    query = db.query(PmoChangeRequest).filter(PmoChangeRequest.project_id == project_id)
    
    if change_id:
        query = query.filter(PmoChangeRequest.id == change_id)
    
    changes = query.all()
    
    impact_analysis = []
    
    for change in changes:
        impacts = {
            'change_id': change.id,
            'change_no': change.change_no,
            'change_type': change.change_type,
            'change_level': change.change_level,
            'title': change.title,
            'status': change.status,
            'impacts': {}
        }
        
        if change.schedule_impact:
            impacts['impacts']['schedule'] = {
                'description': change.schedule_impact,
                'affected_items': [],
                'severity': 'HIGH' if change.change_level == 'CRITICAL' else 'MEDIUM',
            }
            
            if change.status == 'APPROVED':
                affected_tasks = db.query(Task).filter(
                    Task.project_id == project_id,
                    Task.status.in_(['PENDING', 'IN_PROGRESS'])
                ).all()
                
                impacts['impacts']['schedule']['affected_items'] = [
                    {
                        'task_id': task.id,
                        'task_name': task.task_name,
                        'plan_start': task.plan_start.isoformat() if task.plan_start else None,
                        'plan_end': task.plan_end.isoformat() if task.plan_end else None,
                    }
                    for task in affected_tasks[:10]
                ]
        
        if change.cost_impact:
            impacts['impacts']['cost'] = {
                'cost_impact': float(change.cost_impact),
                'description': f"预计成本影响：{change.cost_impact}元",
                'severity': 'HIGH' if abs(float(change.cost_impact or 0)) > project.budget_amount * 0.1 else 'MEDIUM',
            }
        
        if change.resource_impact:
            impacts['impacts']['resource'] = {
                'description': change.resource_impact,
                'affected_resources': [],
                'severity': 'MEDIUM',
            }
            
            if change.status == 'APPROVED':
                affected_allocations = db.query(PmoResourceAllocation).filter(
                    PmoResourceAllocation.project_id == project_id,
                    PmoResourceAllocation.status != 'CANCELLED'
                ).all()
                
                impacts['impacts']['resource']['affected_resources'] = [
                    {
                        'allocation_id': alloc.id,
                        'resource_name': alloc.resource_name,
                        'allocation_percent': alloc.allocation_percent,
                        'start_date': alloc.start_date.isoformat() if alloc.start_date else None,
                        'end_date': alloc.end_date.isoformat() if alloc.end_date else None,
                    }
                    for alloc in affected_allocations[:10]
                ]
        
        related_project_impacts = []
        if change.resource_impact and change.status == 'APPROVED':
            project_resources = db.query(PmoResourceAllocation).filter(
                PmoResourceAllocation.project_id == project_id,
                PmoResourceAllocation.status != 'CANCELLED'
            ).all()
            
            resource_ids = [alloc.resource_id for alloc in project_resources]
            
            if resource_ids:
                shared_projects = (
                    db.query(PmoResourceAllocation.project_id)
                    .filter(
                        PmoResourceAllocation.resource_id.in_(resource_ids),
                        PmoResourceAllocation.project_id != project_id,
                        PmoResourceAllocation.status != 'CANCELLED'
                    )
                    .distinct()
                    .all()
                )
                
                for (related_project_id,) in shared_projects:
                    related_project = db.query(Project).filter(Project.id == related_project_id).first()
                    if related_project:
                        related_project_impacts.append({
                            'project_id': related_project_id,
                            'project_code': related_project.project_code,
                            'project_name': related_project.project_name,
                            'impact_reason': '共享资源可能受影响',
                        })
        
        impacts['impacts']['related_projects'] = {
            'affected_projects': related_project_impacts,
            'count': len(related_project_impacts),
        }
        
        impact_analysis.append(impacts)
    
    total_cost_impact = sum(
        abs(float(change.cost_impact or 0)) 
        for change in changes 
        if change.cost_impact
    )
    
    stats = {
        'total_changes': len(changes),
        'by_type': {},
        'by_level': {},
        'by_status': {},
        'total_cost_impact': total_cost_impact,
        'affected_projects_count': len(set(
            proj['project_id'] 
            for impact in impact_analysis 
            for proj in impact.get('impacts', {}).get('related_projects', {}).get('affected_projects', [])
        )),
    }
    
    for change in changes:
        change_type = change.change_type or 'OTHER'
        if change_type not in stats['by_type']:
            stats['by_type'][change_type] = 0
        stats['by_type'][change_type] += 1
        
        change_level = change.change_level or 'MINOR'
        if change_level not in stats['by_level']:
            stats['by_level'][change_level] = 0
        stats['by_level'][change_level] += 1
        
        change_status = change.status or 'DRAFT'
        if change_status not in stats['by_status']:
            stats['by_status'][change_status] = 0
        stats['by_status'][change_status] += 1
    
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
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)
    
    events = []
    
    # 1. 状态变更历史
    if not event_type or event_type == "STATUS_CHANGE":
        status_logs = db.query(ProjectStatusLog).filter(
            ProjectStatusLog.project_id == project_id
        ).all()
        
        for log in status_logs:
            event = TimelineEvent(
                event_type=log.change_type or "STATUS_CHANGE",
                event_time=log.changed_at or datetime.now(),
                title=f"状态变更: {log.change_type}",
                description=f"{log.old_stage or ''} → {log.new_stage or ''}, {log.old_status or ''} → {log.new_status or ''}",
                user_name=log.changer.username if log.changer else None,
                related_id=log.id,
                related_type="status_log",
            )
            events.append(event)
    
    # 2. 里程碑事件
    if not event_type or event_type == "MILESTONE":
        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id
        ).all()
        
        for milestone in milestones:
            # 里程碑创建
            if milestone.created_at:
                event = TimelineEvent(
                    event_type="MILESTONE_CREATED",
                    event_time=milestone.created_at,
                    title=f"创建里程碑: {milestone.milestone_name}",
                    description=f"计划日期: {milestone.planned_date.isoformat() if milestone.planned_date else '未设置'}",
                    related_id=milestone.id,
                    related_type="milestone",
                )
                events.append(event)
            
            # 里程碑完成
            if milestone.status == "COMPLETED" and milestone.actual_date:
                event = TimelineEvent(
                    event_type="MILESTONE_COMPLETED",
                    event_time=milestone.actual_date,
                    title=f"里程碑完成: {milestone.milestone_name}",
                    description=f"实际完成日期: {milestone.actual_date.isoformat()}",
                    related_id=milestone.id,
                    related_type="milestone",
                )
                events.append(event)
    
    # 3. 任务事件
    if not event_type or event_type == "TASK":
        tasks = db.query(Task).filter(
            Task.project_id == project_id
        ).all()
        
        for task in tasks:
            # 任务创建
            if task.created_at:
                event = TimelineEvent(
                    event_type="TASK_CREATED",
                    event_time=task.created_at,
                    title=f"创建任务: {task.task_name}",
                    description=f"负责人: {task.owner_name or '未分配'}",
                    related_id=task.id,
                    related_type="task",
                )
                events.append(event)
            
            # 任务完成
            if task.status == "COMPLETED" and task.actual_end:
                event = TimelineEvent(
                    event_type="TASK_COMPLETED",
                    event_time=task.actual_end,
                    title=f"任务完成: {task.task_name}",
                    description=f"完成进度: {task.progress_pct}%",
                    related_id=task.id,
                    related_type="task",
                )
                events.append(event)
    
    # 4. 成本记录
    if not event_type or event_type == "COST":
        from app.models.project import ProjectCost
        costs = db.query(ProjectCost).filter(
            ProjectCost.project_id == project_id
        ).all()
        
        for cost in costs:
            if cost.created_at:
                event = TimelineEvent(
                    event_type="COST_RECORDED",
                    event_time=cost.created_at,
                    title=f"成本记录: {cost.cost_name or cost.cost_type}",
                    description=f"金额: {cost.cost_amount}元, 类型: {cost.cost_type}",
                    related_id=cost.id,
                    related_type="cost",
                )
                events.append(event)
    
    # 5. 文档上传
    if not event_type or event_type == "DOCUMENT":
        from app.models.project import ProjectDocument
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()
        
        for doc in documents:
            if doc.created_at:
                event = TimelineEvent(
                    event_type="DOCUMENT_UPLOADED",
                    event_time=doc.created_at,
                    title=f"上传文档: {doc.doc_name}",
                    description=f"类型: {doc.doc_type}, 分类: {doc.doc_category}",
                    related_id=doc.id,
                    related_type="document",
                )
                events.append(event)
    
    # 6. 项目创建
    if project.created_at:
        event = TimelineEvent(
            event_type="PROJECT_CREATED",
            event_time=project.created_at,
            title="项目创建",
            description=f"项目编码: {project.project_code}",
            related_id=project.id,
            related_type="project",
        )
        events.append(event)
    
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
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)
    
    # ========== 基本信息 ==========
    basic_info = {
        "project_code": project.project_code,
        "project_name": project.project_name,
        "customer_name": project.customer_name,
        "pm_name": project.pm_name,
        "stage": project.stage or "S1",
        "status": project.status or "ST01",
        "health": project.health or "H1",
        "progress_pct": float(project.progress_pct or 0),
        "planned_start_date": project.planned_start_date.isoformat() if project.planned_start_date else None,
        "planned_end_date": project.planned_end_date.isoformat() if project.planned_end_date else None,
        "actual_start_date": project.actual_start_date.isoformat() if project.actual_start_date else None,
        "actual_end_date": project.actual_end_date.isoformat() if project.actual_end_date else None,
        "contract_amount": float(project.contract_amount or 0),
        "budget_amount": float(project.budget_amount or 0),
    }
    
    # ========== 进度统计 ==========
    from datetime import date
    today = date.today()
    
    # 计算计划进度
    plan_progress = 0
    if project.planned_start_date and project.planned_end_date:
        total_days = (project.planned_end_date - project.planned_start_date).days
        if total_days > 0:
            elapsed_days = (today - project.planned_start_date).days
            plan_progress = min(100, max(0, (elapsed_days / total_days) * 100))
    
    # 计算进度偏差
    progress_deviation = float(project.progress_pct or 0) - plan_progress
    
    # 计算时间偏差
    time_deviation_days = 0
    if project.planned_end_date:
        time_deviation_days = (today - project.planned_end_date).days
    
    progress_stats = {
        "actual_progress": float(project.progress_pct or 0),
        "plan_progress": plan_progress,
        "progress_deviation": progress_deviation,
        "time_deviation_days": time_deviation_days,
        "is_delayed": time_deviation_days > 0 and project.stage != "S9",
    }
    
    # ========== 成本统计 ==========
    from app.models.project import ProjectCost
    costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()
    
    total_cost = sum(float(cost.amount or 0) for cost in costs)
    cost_by_type = {}
    cost_by_category = {}
    
    for cost in costs:
        cost_type = cost.cost_type or "其他"
        cost_category = cost.cost_category or "其他"
        amount = float(cost.amount or 0)
        
        cost_by_type[cost_type] = cost_by_type.get(cost_type, 0) + amount
        cost_by_category[cost_category] = cost_by_category.get(cost_category, 0) + amount
    
    budget_amount = float(project.budget_amount or 0)
    cost_variance = budget_amount - total_cost if budget_amount > 0 else 0
    cost_variance_rate = (cost_variance / budget_amount * 100) if budget_amount > 0 else 0
    
    cost_stats = {
        "total_cost": total_cost,
        "budget_amount": budget_amount,
        "cost_variance": cost_variance,
        "cost_variance_rate": cost_variance_rate,
        "cost_by_type": cost_by_type,
        "cost_by_category": cost_by_category,
        "is_over_budget": total_cost > budget_amount if budget_amount > 0 else False,
    }
    
    # ========== 任务统计 ==========
    from app.models.progress import Task
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    task_total = len(tasks)
    task_completed = len([t for t in tasks if t.status == "COMPLETED"])
    task_in_progress = len([t for t in tasks if t.status == "IN_PROGRESS"])
    task_pending = len([t for t in tasks if t.status in ["PENDING", "ACCEPTED"]])
    task_blocked = len([t for t in tasks if t.status == "BLOCKED"])
    
    task_avg_progress = sum(float(t.progress_pct or 0) for t in tasks) / task_total if task_total > 0 else 0
    
    task_stats = {
        "total": task_total,
        "completed": task_completed,
        "in_progress": task_in_progress,
        "pending": task_pending,
        "blocked": task_blocked,
        "completion_rate": (task_completed / task_total * 100) if task_total > 0 else 0,
        "avg_progress": task_avg_progress,
    }
    
    # ========== 里程碑统计 ==========
    milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).all()
    
    milestone_total = len(milestones)
    milestone_completed = len([m for m in milestones if m.status == "COMPLETED"])
    milestone_overdue = len([
        m for m in milestones 
        if m.status != "COMPLETED" and m.planned_date and m.planned_date < today
    ])
    milestone_upcoming = len([
        m for m in milestones 
        if m.status != "COMPLETED" and m.planned_date and m.planned_date >= today
    ])
    
    milestone_stats = {
        "total": milestone_total,
        "completed": milestone_completed,
        "overdue": milestone_overdue,
        "upcoming": milestone_upcoming,
        "completion_rate": (milestone_completed / milestone_total * 100) if milestone_total > 0 else 0,
    }
    
    # ========== 风险统计 ==========
    risk_stats = None
    try:
        from app.models.pmo import PmoProjectRisk
        risks = db.query(PmoProjectRisk).filter(PmoProjectRisk.project_id == project_id).all()
        
        risk_total = len(risks)
        risk_high = len([r for r in risks if r.risk_level == "HIGH" and r.status != "CLOSED"])
        risk_critical = len([r for r in risks if r.risk_level == "CRITICAL" and r.status != "CLOSED"])
        risk_open = len([r for r in risks if r.status != "CLOSED"])
        
        risk_stats = {
            "total": risk_total,
            "open": risk_open,
            "high": risk_high,
            "critical": risk_critical,
        }
    except:
        pass
    
    # ========== 问题统计 ==========
    issue_stats = None
    try:
        from app.models.issue import Issue
        issues = db.query(Issue).filter(Issue.project_id == project_id).all()
        
        issue_total = len(issues)
        issue_open = len([i for i in issues if i.status == "OPEN"])
        issue_processing = len([i for i in issues if i.status == "PROCESSING"])
        issue_blocking = len([i for i in issues if i.is_blocking])
        
        issue_stats = {
            "total": issue_total,
            "open": issue_open,
            "processing": issue_processing,
            "blocking": issue_blocking,
        }
    except:
        pass
    
    # ========== 资源使用 ==========
    resource_usage = None
    try:
        from app.models.pmo import PmoResourceAllocation
        allocations = db.query(PmoResourceAllocation).filter(
            PmoResourceAllocation.project_id == project_id
        ).all()
        
        if allocations:
            resource_usage = {
                "total_allocations": len(allocations),
                "by_department": {},
                "by_role": {},
            }
            
            for alloc in allocations:
                dept = alloc.department_name or "未分配"
                role = alloc.role or "未分配"
                
                resource_usage["by_department"][dept] = resource_usage["by_department"].get(dept, 0) + 1
                resource_usage["by_role"][role] = resource_usage["by_role"].get(role, 0) + 1
    except:
        pass
    
    # ========== 最近活动 ==========
    recent_activities = []
    
    # 最近的状态变更
    recent_status_logs = db.query(ProjectStatusLog).filter(
        ProjectStatusLog.project_id == project_id
    ).order_by(desc(ProjectStatusLog.changed_at)).limit(5).all()
    
    for log in recent_status_logs:
        activity = {
            "type": "STATUS_CHANGE",
            "time": log.changed_at.isoformat() if log.changed_at else None,
            "title": f"状态变更：{log.old_status} → {log.new_status}",
            "description": log.change_reason,
        }
        recent_activities.append(activity)
    
    # 最近的里程碑完成
    recent_milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status == "COMPLETED"
    ).order_by(desc(ProjectMilestone.actual_date)).limit(3).all()
    
    for milestone in recent_milestones:
        activity = {
            "type": "MILESTONE",
            "time": milestone.actual_date.isoformat() if milestone.actual_date else None,
            "title": f"里程碑完成：{milestone.milestone_name}",
            "description": None,
        }
        recent_activities.append(activity)
    
    # 按时间排序
    recent_activities.sort(key=lambda x: x.get("time") or "", reverse=True)
    recent_activities = recent_activities[:10]
    
    # ========== 关键指标 ==========
    key_metrics = {
        "health_score": 100 if project.health == "H1" else (75 if project.health == "H2" else (50 if project.health == "H3" else 25)),
        "progress_score": float(project.progress_pct or 0),
        "schedule_score": 100 - abs(progress_deviation) if abs(progress_deviation) <= 20 else max(0, 100 - abs(progress_deviation) * 2),
        "cost_score": 100 - abs(cost_variance_rate) if abs(cost_variance_rate) <= 10 else max(0, 100 - abs(cost_variance_rate) * 2),
        "quality_score": (task_completed / task_total * 100) if task_total > 0 else 100,
    }
    
    # 计算综合得分
    key_metrics["overall_score"] = (
        key_metrics["health_score"] * 0.3 +
        key_metrics["progress_score"] * 0.25 +
        key_metrics["schedule_score"] * 0.2 +
        key_metrics["cost_score"] * 0.15 +
        key_metrics["quality_score"] * 0.1
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
    """G1: S1→S2 阶段门校验 - 需求采集表完整、客户信息齐全"""
    missing = []
    
    if not project.customer_id:
        missing.append("客户信息未填写")
    elif not project.customer_name:
        missing.append("客户名称未填写")
    
    if not project.requirements:
        missing.append("需求采集表未填写")
    
    return (len(missing) == 0, missing)


def check_gate_s2_to_s3(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """G2: S2→S3 阶段门校验 - 需求规格书确认、验收标准明确"""
    missing = []
    
    # 检查是否有需求规格书文档
    from app.models.project import ProjectDocument
    spec_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project.id,
        ProjectDocument.doc_type.in_(["REQUIREMENT", "SPECIFICATION"]),
        ProjectDocument.status == "APPROVED"
    ).count()
    
    if spec_docs == 0:
        missing.append("需求规格书未确认")
    
    # 检查验收标准
    if not project.requirements or "验收标准" not in (project.requirements or ""):
        missing.append("验收标准未明确")
    
    return (len(missing) == 0, missing)


def check_gate_s3_to_s4(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """G3: S3→S4 阶段门校验 - 立项评审通过、合同签订"""
    missing = []
    
    # 检查合同是否签订
    if not project.contract_no:
        missing.append("合同编号未填写")
    
    if not project.contract_date:
        missing.append("合同签订日期未填写")
    
    if not project.contract_amount or project.contract_amount <= 0:
        missing.append("合同金额未填写或无效")
    
    # 检查是否有立项评审记录（可以通过PMO模块检查）
    from app.models.pmo import PmoProjectRisk
    # 这里简化处理，实际应该检查立项评审流程
    
    return (len(missing) == 0, missing)


def check_gate_s4_to_s5(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """G4: S4→S5 阶段门校验 - 方案评审通过、BOM发布"""
    missing = []
    
    # 检查BOM是否发布
    from app.models.material import BomHeader
    released_boms = db.query(BomHeader).filter(
        BomHeader.project_id == project.id,
        BomHeader.status == "RELEASED"
    ).count()
    
    if released_boms == 0:
        missing.append("BOM未发布")
    
    # 检查方案文档
    from app.models.project import ProjectDocument
    design_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project.id,
        ProjectDocument.doc_type.in_(["DESIGN", "SCHEME"]),
        ProjectDocument.status == "APPROVED"
    ).count()
    
    if design_docs == 0:
        missing.append("方案设计文档未评审通过")
    
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
        
        # 检查关键物料
        for item in bom_items:
            material = item.material
            if material and material.is_key_material:
                # 计算可用数量 = 当前库存 + 已到货数量
                available_qty = Decimal(str(material.current_stock or 0)) + Decimal(str(item.received_qty or 0))
                required_qty = Decimal(str(item.quantity or 0))
                
                if available_qty < required_qty:
                    missing.append(f"关键物料 {material.material_name} 未到货（需求：{required_qty}，可用：{available_qty}）")
    
    return (len(missing) == 0, missing)


def check_gate_s6_to_s7(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """G6: S6→S7 阶段门校验 - 装配完成、联调通过"""
    missing = []
    
    # 检查所有机台的装配状态
    machines = db.query(Machine).filter(Machine.project_id == project.id).all()
    
    for machine in machines:
        if machine.progress_pct < 100:
            missing.append(f"机台 {machine.machine_code} 装配未完成（进度：{machine.progress_pct}%）")
    
    # 检查是否有联调报告
    from app.models.project import ProjectDocument
    debug_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project.id,
        ProjectDocument.doc_type.in_(["DEBUG", "TEST"]),
        ProjectDocument.status == "APPROVED"
    ).count()
    
    if debug_docs == 0:
        missing.append("联调测试报告未提交或未通过")
    
    return (len(missing) == 0, missing)


def check_gate_s7_to_s8(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """G7: S7→S8 阶段门校验 - FAT验收通过"""
    missing = []
    
    # 检查FAT验收单
    from app.models.acceptance import AcceptanceOrder
    fat_orders = db.query(AcceptanceOrder).filter(
        AcceptanceOrder.project_id == project.id,
        AcceptanceOrder.acceptance_type == "FAT",
        AcceptanceOrder.status == "COMPLETED"
    ).count()
    
    if fat_orders == 0:
        missing.append("FAT验收未通过")
    
    return (len(missing) == 0, missing)


def check_gate_s8_to_s9(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """G8: S8→S9 阶段门校验 - 终验收通过、回款达标"""
    missing = []
    
    # 检查SAT验收单
    from app.models.acceptance import AcceptanceOrder
    sat_orders = db.query(AcceptanceOrder).filter(
        AcceptanceOrder.project_id == project.id,
        AcceptanceOrder.acceptance_type == "SAT",
        AcceptanceOrder.status == "COMPLETED"
    ).count()
    
    if sat_orders == 0:
        missing.append("SAT终验收未通过")
    
    # 检查回款情况
    payment_plans = db.query(ProjectPaymentPlan).filter(
        ProjectPaymentPlan.project_id == project.id,
        ProjectPaymentPlan.status == "PAID"
    ).all()
    
    total_paid = sum(float(plan.actual_amount or 0) for plan in payment_plans)
    contract_amount = float(project.contract_amount or 0)
    
    if contract_amount > 0:
        payment_rate = (total_paid / contract_amount) * 100
        if payment_rate < 80:  # 回款率需≥80%
            missing.append(f"回款率 {payment_rate:.1f}%，需≥80%")
    
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
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)
    
    # 验证目标阶段
    valid_stages = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    if advance_request.target_stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"无效的目标阶段。有效值：{', '.join(valid_stages)}"
        )
    
    # 检查阶段是否向前推进
    current_stage = project.stage or "S1"
    current_stage_num = int(current_stage[1]) if len(current_stage) > 1 else 1
    target_stage_num = int(advance_request.target_stage[1]) if len(advance_request.target_stage) > 1 else 1
    
    if target_stage_num <= current_stage_num:
        raise HTTPException(
            status_code=400,
            detail=f"目标阶段 {advance_request.target_stage} 不能早于或等于当前阶段 {current_stage}"
        )
    
    # 阶段门校验（除非跳过）
    gate_passed = True
    missing_items = []
    
    if not advance_request.skip_gate_check:
        # 只有管理员可以跳过阶段门校验
        if not current_user.is_superuser:
            gate_passed, missing_items = check_gate(db, project, advance_request.target_stage)
            
            if not gate_passed:
                return ResponseModel(
                    code=400,
                    message="阶段门校验未通过",
                    data={
                        "project_id": project_id,
                        "target_stage": advance_request.target_stage,
                        "gate_passed": False,
                        "missing_items": missing_items,
                    }
                )
    else:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="只有管理员可以跳过阶段门校验"
            )
    
    # 记录旧阶段
    old_stage = current_stage
    old_status = project.status
    
    # 更新项目阶段
    project.stage = advance_request.target_stage
    
    # 根据阶段自动更新状态（可选）
    stage_status_map = {
        'S1': 'ST01',
        'S2': 'ST03',
        'S3': 'ST05',
        'S4': 'ST07',
        'S5': 'ST10',
        'S6': 'ST15',
        'S7': 'ST20',
        'S8': 'ST25',
        'S9': 'ST30',
    }
    
    new_status = stage_status_map.get(advance_request.target_stage, old_status)
    if new_status != old_status:
        project.status = new_status
    
    db.add(project)
    
    # 记录状态变更历史
    status_log = ProjectStatusLog(
        project_id=project_id,
        old_stage=old_stage,
        new_stage=advance_request.target_stage,
        old_status=old_status,
        new_status=new_status,
        old_health=project.health,
        new_health=project.health,
        change_type="STAGE_ADVANCE",
        change_reason=advance_request.reason,
        changed_by=current_user.id,
        changed_at=datetime.now()
    )
    db.add(status_log)
    
    # 如果项目进入S9阶段或状态变为ST30，自动生成成本复盘报告
    if advance_request.target_stage == "S9" or new_status == "ST30":
        try:
            from app.services.cost_review_service import CostReviewService
            # 自动生成成本复盘报告（如果不存在）
            existing_review = db.query(ProjectReview).filter(
                ProjectReview.project_id == project_id,
                ProjectReview.review_type == "POST_MORTEM"
            ).first()
            
            if not existing_review:
                CostReviewService.generate_cost_review_report(
                    db, project_id, current_user.id
                )
        except Exception as e:
            # 如果生成复盘报告失败，记录日志但不影响阶段更新
            import logging
            logging.warning(f"自动生成成本复盘报告失败：{str(e)}")
    
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
            "gate_check_result": {
                "passed": gate_passed,
                "missing_items": missing_items,
            } if not advance_request.skip_gate_check else None,
        }
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
