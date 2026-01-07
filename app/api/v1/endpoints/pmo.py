# -*- coding: utf-8 -*-
"""
PMO 项目管理部 API endpoints
包含：立项管理、项目阶段门管理、风险管理、项目结项管理、PMO驾驶舱
"""
from typing import Any, List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.project import Project, Customer
from app.models.pmo import (
    PmoProjectInitiation, PmoProjectPhase, PmoProjectRisk,
    PmoProjectClosure, PmoResourceAllocation, PmoMeeting
)
from app.schemas.pmo import (
    InitiationCreate, InitiationUpdate, InitiationResponse,
    InitiationApproveRequest, InitiationRejectRequest,
    PhaseResponse, PhaseEntryCheckRequest, PhaseExitCheckRequest,
    PhaseReviewRequest, PhaseAdvanceRequest,
    RiskCreate, RiskAssessRequest, RiskResponseRequest,
    RiskStatusUpdateRequest, RiskCloseRequest, RiskResponse,
    ClosureCreate, ClosureReviewRequest, ClosureLessonsRequest, ClosureResponse,
    DashboardResponse, DashboardSummary, WeeklyReportResponse,
    ResourceOverviewResponse, RiskWallResponse,
    MeetingCreate, MeetingUpdate, MeetingMinutesRequest, MeetingResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


def generate_initiation_no(db: Session) -> str:
    """生成立项申请编号：INIT-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_init = (
        db.query(PmoProjectInitiation)
        .filter(PmoProjectInitiation.application_no.like(f"INIT-{today}-%"))
        .order_by(desc(PmoProjectInitiation.application_no))
        .first()
    )
    if max_init:
        seq = int(max_init.application_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"INIT-{today}-{seq:03d}"


def generate_risk_no(db: Session) -> str:
    """生成风险编号：RISK-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_risk = (
        db.query(PmoProjectRisk)
        .filter(PmoProjectRisk.risk_no.like(f"RISK-{today}-%"))
        .order_by(desc(PmoProjectRisk.risk_no))
        .first()
    )
    if max_risk:
        seq = int(max_risk.risk_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"RISK-{today}-{seq:03d}"


# ==================== 立项管理 ====================

@router.get("/pmo/initiations", response_model=PaginatedResponse)
def read_initiations(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（申请编号/项目名称）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    applicant_id: Optional[int] = Query(None, description="申请人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    立项申请列表
    """
    query = db.query(PmoProjectInitiation)
    
    if keyword:
        query = query.filter(
            or_(
                PmoProjectInitiation.application_no.like(f"%{keyword}%"),
                PmoProjectInitiation.project_name.like(f"%{keyword}%"),
            )
        )
    
    if status:
        query = query.filter(PmoProjectInitiation.status == status)
    
    if applicant_id:
        query = query.filter(PmoProjectInitiation.applicant_id == applicant_id)
    
    total = query.count()
    offset = (page - 1) * page_size
    initiations = query.order_by(desc(PmoProjectInitiation.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for init in initiations:
        items.append(InitiationResponse(
            id=init.id,
            application_no=init.application_no,
            project_id=init.project_id,
            project_name=init.project_name,
            project_type=init.project_type,
            project_level=init.project_level,
            customer_name=init.customer_name,
            contract_no=init.contract_no,
            contract_amount=float(init.contract_amount) if init.contract_amount else None,
            required_start_date=init.required_start_date,
            required_end_date=init.required_end_date,
            technical_solution_id=init.technical_solution_id,
            requirement_summary=init.requirement_summary,
            technical_difficulty=init.technical_difficulty,
            estimated_hours=init.estimated_hours,
            resource_requirements=init.resource_requirements,
            risk_assessment=init.risk_assessment,
            applicant_id=init.applicant_id,
            applicant_name=init.applicant_name,
            apply_time=init.apply_time,
            status=init.status,
            review_result=init.review_result,
            approved_pm_id=init.approved_pm_id,
            approved_level=init.approved_level,
            approved_at=init.approved_at,
            approved_by=init.approved_by,
            created_at=init.created_at,
            updated_at=init.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/pmo/initiations", response_model=InitiationResponse, status_code=status.HTTP_201_CREATED)
def create_initiation(
    *,
    db: Session = Depends(deps.get_db),
    initiation_in: InitiationCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建立项申请
    """
    initiation = PmoProjectInitiation(
        application_no=generate_initiation_no(db),
        project_name=initiation_in.project_name,
        project_type=initiation_in.project_type,
        project_level=initiation_in.project_level,
        customer_name=initiation_in.customer_name,
        contract_no=initiation_in.contract_no,
        contract_amount=initiation_in.contract_amount,
        required_start_date=initiation_in.required_start_date,
        required_end_date=initiation_in.required_end_date,
        technical_solution_id=initiation_in.technical_solution_id,
        requirement_summary=initiation_in.requirement_summary,
        technical_difficulty=initiation_in.technical_difficulty,
        estimated_hours=initiation_in.estimated_hours,
        resource_requirements=initiation_in.resource_requirements,
        risk_assessment=initiation_in.risk_assessment,
        applicant_id=current_user.id,
        applicant_name=current_user.real_name or current_user.username,
        apply_time=datetime.now(),
        status='DRAFT'
    )
    
    db.add(initiation)
    db.commit()
    db.refresh(initiation)
    
    return InitiationResponse(
        id=initiation.id,
        application_no=initiation.application_no,
        project_id=initiation.project_id,
        project_name=initiation.project_name,
        project_type=initiation.project_type,
        project_level=initiation.project_level,
        customer_name=initiation.customer_name,
        contract_no=initiation.contract_no,
        contract_amount=float(initiation.contract_amount) if initiation.contract_amount else None,
        required_start_date=initiation.required_start_date,
        required_end_date=initiation.required_end_date,
        technical_solution_id=initiation.technical_solution_id,
        requirement_summary=initiation.requirement_summary,
        technical_difficulty=initiation.technical_difficulty,
        estimated_hours=initiation.estimated_hours,
        resource_requirements=initiation.resource_requirements,
        risk_assessment=initiation.risk_assessment,
        applicant_id=initiation.applicant_id,
        applicant_name=initiation.applicant_name,
        apply_time=initiation.apply_time,
        status=initiation.status,
        review_result=initiation.review_result,
        approved_pm_id=initiation.approved_pm_id,
        approved_level=initiation.approved_level,
        approved_at=initiation.approved_at,
        approved_by=initiation.approved_by,
        created_at=initiation.created_at,
        updated_at=initiation.updated_at,
    )


@router.get("/pmo/initiations/{initiation_id}", response_model=InitiationResponse)
def read_initiation(
    *,
    db: Session = Depends(deps.get_db),
    initiation_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    立项申请详情
    """
    initiation = db.query(PmoProjectInitiation).filter(PmoProjectInitiation.id == initiation_id).first()
    if not initiation:
        raise HTTPException(status_code=404, detail="立项申请不存在")
    
    return InitiationResponse(
        id=initiation.id,
        application_no=initiation.application_no,
        project_id=initiation.project_id,
        project_name=initiation.project_name,
        project_type=initiation.project_type,
        project_level=initiation.project_level,
        customer_name=initiation.customer_name,
        contract_no=initiation.contract_no,
        contract_amount=float(initiation.contract_amount) if initiation.contract_amount else None,
        required_start_date=initiation.required_start_date,
        required_end_date=initiation.required_end_date,
        technical_solution_id=initiation.technical_solution_id,
        requirement_summary=initiation.requirement_summary,
        technical_difficulty=initiation.technical_difficulty,
        estimated_hours=initiation.estimated_hours,
        resource_requirements=initiation.resource_requirements,
        risk_assessment=initiation.risk_assessment,
        applicant_id=initiation.applicant_id,
        applicant_name=initiation.applicant_name,
        apply_time=initiation.apply_time,
        status=initiation.status,
        review_result=initiation.review_result,
        approved_pm_id=initiation.approved_pm_id,
        approved_level=initiation.approved_level,
        approved_at=initiation.approved_at,
        approved_by=initiation.approved_by,
        created_at=initiation.created_at,
        updated_at=initiation.updated_at,
    )


@router.put("/pmo/initiations/{initiation_id}", response_model=InitiationResponse)
def update_initiation(
    *,
    db: Session = Depends(deps.get_db),
    initiation_id: int,
    initiation_in: InitiationUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新立项申请
    """
    initiation = db.query(PmoProjectInitiation).filter(PmoProjectInitiation.id == initiation_id).first()
    if not initiation:
        raise HTTPException(status_code=404, detail="立项申请不存在")
    
    if initiation.status != 'DRAFT':
        raise HTTPException(status_code=400, detail="只有草稿状态的申请才能修改")
    
    update_data = initiation_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(initiation, field, value)
    
    db.add(initiation)
    db.commit()
    db.refresh(initiation)
    
    return read_initiation(db=db, initiation_id=initiation_id, current_user=current_user)


@router.put("/pmo/initiations/{initiation_id}/submit", response_model=ResponseModel)
def submit_initiation(
    *,
    db: Session = Depends(deps.get_db),
    initiation_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交立项评审
    """
    initiation = db.query(PmoProjectInitiation).filter(PmoProjectInitiation.id == initiation_id).first()
    if not initiation:
        raise HTTPException(status_code=404, detail="立项申请不存在")
    
    if initiation.status != 'DRAFT':
        raise HTTPException(status_code=400, detail="只有草稿状态的申请才能提交")
    
    initiation.status = 'SUBMITTED'
    db.add(initiation)
    db.commit()
    
    return ResponseModel(code=200, message="提交成功")


@router.put("/pmo/initiations/{initiation_id}/approve", response_model=ResponseModel)
def approve_initiation(
    *,
    db: Session = Depends(deps.get_db),
    initiation_id: int,
    approve_request: InitiationApproveRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    立项评审通过
    """
    initiation = db.query(PmoProjectInitiation).filter(PmoProjectInitiation.id == initiation_id).first()
    if not initiation:
        raise HTTPException(status_code=404, detail="立项申请不存在")
    
    if initiation.status not in ['SUBMITTED', 'REVIEWING']:
        raise HTTPException(status_code=400, detail="只有已提交或评审中的申请才能审批")
    
    initiation.status = 'APPROVED'
    initiation.review_result = approve_request.review_result
    initiation.approved_pm_id = approve_request.approved_pm_id
    initiation.approved_level = approve_request.approved_level
    initiation.approved_at = datetime.now()
    initiation.approved_by = current_user.id
    
    # 如果指定了项目经理，创建项目
    if approve_request.approved_pm_id:
        # 生成项目编码（简化实现）
        from datetime import date
        today = date.today()
        project_code = f"PJ{today.strftime('%y%m%d')}{initiation.id:03d}"
        
        # 检查项目编码是否已存在
        existing = db.query(Project).filter(Project.project_code == project_code).first()
        if existing:
            project_code = f"PJ{today.strftime('%y%m%d')}{initiation.id:04d}"
        
        # 查找或创建客户
        customer = db.query(Customer).filter(Customer.customer_name == initiation.customer_name).first()
        customer_id = customer.id if customer else None
        
        # 创建项目
        project = Project(
            project_code=project_code,
            project_name=initiation.project_name,
            customer_id=customer_id,
            customer_name=initiation.customer_name,
            contract_no=initiation.contract_no,
            contract_amount=initiation.contract_amount or Decimal("0"),
            contract_date=initiation.required_start_date,
            planned_start_date=initiation.required_start_date,
            planned_end_date=initiation.required_end_date,
            pm_id=approve_request.approved_pm_id,
            project_type=initiation.project_type,
            stage='S1',
            status='ST01',
            health='H1',
        )
        
        # 填充项目经理信息
        pm = db.query(User).filter(User.id == approve_request.approved_pm_id).first()
        if pm:
            project.pm_name = pm.real_name or pm.username
        
        db.add(project)
        db.flush()
        
        # 关联立项申请和项目
        initiation.project_id = project.id
        
        # 初始化项目阶段
        from app.utils.project_utils import init_project_stages
        init_project_stages(db, project.id)
    
    db.add(initiation)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="审批通过",
        data={"project_id": initiation.project_id} if initiation.project_id else None
    )


@router.put("/pmo/initiations/{initiation_id}/reject", response_model=ResponseModel)
def reject_initiation(
    *,
    db: Session = Depends(deps.get_db),
    initiation_id: int,
    reject_request: InitiationRejectRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    立项评审驳回
    """
    initiation = db.query(PmoProjectInitiation).filter(PmoProjectInitiation.id == initiation_id).first()
    if not initiation:
        raise HTTPException(status_code=404, detail="立项申请不存在")
    
    if initiation.status not in ['SUBMITTED', 'REVIEWING']:
        raise HTTPException(status_code=400, detail="只有已提交或评审中的申请才能驳回")
    
    initiation.status = 'REJECTED'
    initiation.review_result = reject_request.review_result
    initiation.approved_at = datetime.now()
    initiation.approved_by = current_user.id
    
    db.add(initiation)
    db.commit()
    
    return ResponseModel(code=200, message="已驳回")


# ==================== 项目阶段 ====================

@router.get("/pmo/projects/{project_id}/phases", response_model=List[PhaseResponse])
def read_project_phases(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目阶段列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    phases = db.query(PmoProjectPhase).filter(
        PmoProjectPhase.project_id == project_id
    ).order_by(PmoProjectPhase.phase_order).all()
    
    result = []
    for phase in phases:
        result.append(PhaseResponse(
            id=phase.id,
            project_id=phase.project_id,
            phase_code=phase.phase_code,
            phase_name=phase.phase_name,
            phase_order=phase.phase_order,
            plan_start_date=phase.plan_start_date,
            plan_end_date=phase.plan_end_date,
            actual_start_date=phase.actual_start_date,
            actual_end_date=phase.actual_end_date,
            status=phase.status,
            progress=phase.progress,
            entry_criteria=phase.entry_criteria,
            exit_criteria=phase.exit_criteria,
            entry_check_result=phase.entry_check_result,
            exit_check_result=phase.exit_check_result,
            review_required=phase.review_required,
            review_date=phase.review_date,
            review_result=phase.review_result,
            review_notes=phase.review_notes,
            created_at=phase.created_at,
            updated_at=phase.updated_at,
        ))
    
    return result


@router.post("/pmo/phases/{phase_id}/entry-check", response_model=PhaseResponse)
def phase_entry_check(
    *,
    db: Session = Depends(deps.get_db),
    phase_id: int,
    check_request: PhaseEntryCheckRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    阶段入口检查
    """
    phase = db.query(PmoProjectPhase).filter(PmoProjectPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    phase.entry_check_result = check_request.check_result
    if check_request.notes:
        # 可以追加到现有结果中
        if phase.entry_check_result:
            phase.entry_check_result += f"\n{check_request.notes}"
        else:
            phase.entry_check_result = check_request.notes
    
    db.add(phase)
    db.commit()
    db.refresh(phase)
    
    return PhaseResponse(
        id=phase.id,
        project_id=phase.project_id,
        phase_code=phase.phase_code,
        phase_name=phase.phase_name,
        phase_order=phase.phase_order,
        plan_start_date=phase.plan_start_date,
        plan_end_date=phase.plan_end_date,
        actual_start_date=phase.actual_start_date,
        actual_end_date=phase.actual_end_date,
        status=phase.status,
        progress=phase.progress,
        entry_criteria=phase.entry_criteria,
        exit_criteria=phase.exit_criteria,
        entry_check_result=phase.entry_check_result,
        exit_check_result=phase.exit_check_result,
        review_required=phase.review_required,
        review_date=phase.review_date,
        review_result=phase.review_result,
        review_notes=phase.review_notes,
        created_at=phase.created_at,
        updated_at=phase.updated_at,
    )


@router.post("/pmo/phases/{phase_id}/exit-check", response_model=PhaseResponse)
def phase_exit_check(
    *,
    db: Session = Depends(deps.get_db),
    phase_id: int,
    check_request: PhaseExitCheckRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    阶段出口检查
    """
    phase = db.query(PmoProjectPhase).filter(PmoProjectPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    phase.exit_check_result = check_request.check_result
    if check_request.notes:
        if phase.exit_check_result:
            phase.exit_check_result += f"\n{check_request.notes}"
        else:
            phase.exit_check_result = check_request.notes
    
    db.add(phase)
    db.commit()
    db.refresh(phase)
    
    return PhaseResponse(
        id=phase.id,
        project_id=phase.project_id,
        phase_code=phase.phase_code,
        phase_name=phase.phase_name,
        phase_order=phase.phase_order,
        plan_start_date=phase.plan_start_date,
        plan_end_date=phase.plan_end_date,
        actual_start_date=phase.actual_start_date,
        actual_end_date=phase.actual_end_date,
        status=phase.status,
        progress=phase.progress,
        entry_criteria=phase.entry_criteria,
        exit_criteria=phase.exit_criteria,
        entry_check_result=phase.entry_check_result,
        exit_check_result=phase.exit_check_result,
        review_required=phase.review_required,
        review_date=phase.review_date,
        review_result=phase.review_result,
        review_notes=phase.review_notes,
        created_at=phase.created_at,
        updated_at=phase.updated_at,
    )


@router.post("/pmo/phases/{phase_id}/review", response_model=PhaseResponse)
def phase_review(
    *,
    db: Session = Depends(deps.get_db),
    phase_id: int,
    review_request: PhaseReviewRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    阶段评审
    """
    phase = db.query(PmoProjectPhase).filter(PmoProjectPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    phase.review_result = review_request.review_result
    phase.review_notes = review_request.review_notes
    phase.review_date = date.today()
    
    db.add(phase)
    db.commit()
    db.refresh(phase)
    
    return PhaseResponse(
        id=phase.id,
        project_id=phase.project_id,
        phase_code=phase.phase_code,
        phase_name=phase.phase_name,
        phase_order=phase.phase_order,
        plan_start_date=phase.plan_start_date,
        plan_end_date=phase.plan_end_date,
        actual_start_date=phase.actual_start_date,
        actual_end_date=phase.actual_end_date,
        status=phase.status,
        progress=phase.progress,
        entry_criteria=phase.entry_criteria,
        exit_criteria=phase.exit_criteria,
        entry_check_result=phase.entry_check_result,
        exit_check_result=phase.exit_check_result,
        review_required=phase.review_required,
        review_date=phase.review_date,
        review_result=phase.review_result,
        review_notes=phase.review_notes,
        created_at=phase.created_at,
        updated_at=phase.updated_at,
    )


@router.put("/pmo/phases/{phase_id}/advance", response_model=PhaseResponse)
def phase_advance(
    *,
    db: Session = Depends(deps.get_db),
    phase_id: int,
    advance_request: PhaseAdvanceRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    阶段推进
    """
    phase = db.query(PmoProjectPhase).filter(PmoProjectPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="阶段不存在")
    
    if advance_request.actual_start_date:
        phase.actual_start_date = advance_request.actual_start_date
        phase.status = 'IN_PROGRESS'
    
    # TODO: 可以添加推进到下一阶段的逻辑
    
    db.add(phase)
    db.commit()
    db.refresh(phase)
    
    return PhaseResponse(
        id=phase.id,
        project_id=phase.project_id,
        phase_code=phase.phase_code,
        phase_name=phase.phase_name,
        phase_order=phase.phase_order,
        plan_start_date=phase.plan_start_date,
        plan_end_date=phase.plan_end_date,
        actual_start_date=phase.actual_start_date,
        actual_end_date=phase.actual_end_date,
        status=phase.status,
        progress=phase.progress,
        entry_criteria=phase.entry_criteria,
        exit_criteria=phase.exit_criteria,
        entry_check_result=phase.entry_check_result,
        exit_check_result=phase.exit_check_result,
        review_required=phase.review_required,
        review_date=phase.review_date,
        review_result=phase.review_result,
        review_notes=phase.review_notes,
        created_at=phase.created_at,
        updated_at=phase.updated_at,
    )


# ==================== 风险管理 ====================

@router.get("/pmo/projects/{project_id}/risks", response_model=List[RiskResponse])
def read_project_risks(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    risk_level: Optional[str] = Query(None, description="风险等级筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    风险列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    query = db.query(PmoProjectRisk).filter(PmoProjectRisk.project_id == project_id)
    
    if status:
        query = query.filter(PmoProjectRisk.status == status)
    
    if risk_level:
        query = query.filter(PmoProjectRisk.risk_level == risk_level)
    
    risks = query.order_by(desc(PmoProjectRisk.created_at)).all()
    
    result = []
    for risk in risks:
        result.append(RiskResponse(
            id=risk.id,
            project_id=risk.project_id,
            risk_no=risk.risk_no,
            risk_category=risk.risk_category,
            risk_name=risk.risk_name,
            description=risk.description,
            probability=risk.probability,
            impact=risk.impact,
            risk_level=risk.risk_level,
            response_strategy=risk.response_strategy,
            response_plan=risk.response_plan,
            owner_id=risk.owner_id,
            owner_name=risk.owner_name,
            status=risk.status,
            follow_up_date=risk.follow_up_date,
            last_update=risk.last_update,
            trigger_condition=risk.trigger_condition,
            is_triggered=risk.is_triggered,
            triggered_date=risk.triggered_date,
            closed_date=risk.closed_date,
            closed_reason=risk.closed_reason,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
        ))
    
    return result


@router.post("/pmo/projects/{project_id}/risks", response_model=RiskResponse, status_code=status.HTTP_201_CREATED)
def create_risk(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    risk_in: RiskCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建风险
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 计算风险等级
    risk_level = None
    if risk_in.probability and risk_in.impact:
        if risk_in.probability == 'HIGH' and risk_in.impact == 'HIGH':
            risk_level = 'CRITICAL'
        elif risk_in.probability == 'HIGH' or risk_in.impact == 'HIGH':
            risk_level = 'HIGH'
        elif risk_in.probability == 'MEDIUM' or risk_in.impact == 'MEDIUM':
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
    
    owner_name = None
    if risk_in.owner_id:
        owner = db.query(User).filter(User.id == risk_in.owner_id).first()
        owner_name = owner.real_name or owner.username if owner else None
    
    risk = PmoProjectRisk(
        project_id=project_id,
        risk_no=generate_risk_no(db),
        risk_category=risk_in.risk_category,
        risk_name=risk_in.risk_name,
        description=risk_in.description,
        probability=risk_in.probability,
        impact=risk_in.impact,
        risk_level=risk_level,
        owner_id=risk_in.owner_id,
        owner_name=owner_name,
        trigger_condition=risk_in.trigger_condition,
        status='IDENTIFIED',
        is_triggered=False
    )
    
    db.add(risk)
    db.commit()
    db.refresh(risk)
    
    return RiskResponse(
        id=risk.id,
        project_id=risk.project_id,
        risk_no=risk.risk_no,
        risk_category=risk.risk_category,
        risk_name=risk.risk_name,
        description=risk.description,
        probability=risk.probability,
        impact=risk.impact,
        risk_level=risk.risk_level,
        response_strategy=risk.response_strategy,
        response_plan=risk.response_plan,
        owner_id=risk.owner_id,
        owner_name=risk.owner_name,
        status=risk.status,
        follow_up_date=risk.follow_up_date,
        last_update=risk.last_update,
        trigger_condition=risk.trigger_condition,
        is_triggered=risk.is_triggered,
        triggered_date=risk.triggered_date,
        closed_date=risk.closed_date,
        closed_reason=risk.closed_reason,
        created_at=risk.created_at,
        updated_at=risk.updated_at,
    )


@router.put("/pmo/risks/{risk_id}/assess", response_model=RiskResponse)
def assess_risk(
    *,
    db: Session = Depends(deps.get_db),
    risk_id: int,
    assess_request: RiskAssessRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    风险评估
    """
    risk = db.query(PmoProjectRisk).filter(PmoProjectRisk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")
    
    risk.probability = assess_request.probability
    risk.impact = assess_request.impact
    
    # 计算风险等级
    if assess_request.risk_level:
        risk.risk_level = assess_request.risk_level
    else:
        if assess_request.probability == 'HIGH' and assess_request.impact == 'HIGH':
            risk.risk_level = 'CRITICAL'
        elif assess_request.probability == 'HIGH' or assess_request.impact == 'HIGH':
            risk.risk_level = 'HIGH'
        elif assess_request.probability == 'MEDIUM' or assess_request.impact == 'MEDIUM':
            risk.risk_level = 'MEDIUM'
        else:
            risk.risk_level = 'LOW'
    
    risk.status = 'ANALYZING'
    
    db.add(risk)
    db.commit()
    db.refresh(risk)
    
    return RiskResponse(
        id=risk.id,
        project_id=risk.project_id,
        risk_no=risk.risk_no,
        risk_category=risk.risk_category,
        risk_name=risk.risk_name,
        description=risk.description,
        probability=risk.probability,
        impact=risk.impact,
        risk_level=risk.risk_level,
        response_strategy=risk.response_strategy,
        response_plan=risk.response_plan,
        owner_id=risk.owner_id,
        owner_name=risk.owner_name,
        status=risk.status,
        follow_up_date=risk.follow_up_date,
        last_update=risk.last_update,
        trigger_condition=risk.trigger_condition,
        is_triggered=risk.is_triggered,
        triggered_date=risk.triggered_date,
        closed_date=risk.closed_date,
        closed_reason=risk.closed_reason,
        created_at=risk.created_at,
        updated_at=risk.updated_at,
    )


@router.put("/pmo/risks/{risk_id}/response", response_model=RiskResponse)
def update_risk_response(
    *,
    db: Session = Depends(deps.get_db),
    risk_id: int,
    response_request: RiskResponseRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    风险应对计划
    """
    risk = db.query(PmoProjectRisk).filter(PmoProjectRisk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")
    
    risk.response_strategy = response_request.response_strategy
    risk.response_plan = response_request.response_plan
    
    if response_request.owner_id:
        risk.owner_id = response_request.owner_id
        owner = db.query(User).filter(User.id == response_request.owner_id).first()
        risk.owner_name = owner.real_name or owner.username if owner else None
    
    risk.status = 'RESPONDING'
    
    db.add(risk)
    db.commit()
    db.refresh(risk)
    
    return RiskResponse(
        id=risk.id,
        project_id=risk.project_id,
        risk_no=risk.risk_no,
        risk_category=risk.risk_category,
        risk_name=risk.risk_name,
        description=risk.description,
        probability=risk.probability,
        impact=risk.impact,
        risk_level=risk.risk_level,
        response_strategy=risk.response_strategy,
        response_plan=risk.response_plan,
        owner_id=risk.owner_id,
        owner_name=risk.owner_name,
        status=risk.status,
        follow_up_date=risk.follow_up_date,
        last_update=risk.last_update,
        trigger_condition=risk.trigger_condition,
        is_triggered=risk.is_triggered,
        triggered_date=risk.triggered_date,
        closed_date=risk.closed_date,
        closed_reason=risk.closed_reason,
        created_at=risk.created_at,
        updated_at=risk.updated_at,
    )


@router.put("/pmo/risks/{risk_id}/status", response_model=RiskResponse)
def update_risk_status(
    *,
    db: Session = Depends(deps.get_db),
    risk_id: int,
    status_request: RiskStatusUpdateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    风险状态更新
    """
    risk = db.query(PmoProjectRisk).filter(PmoProjectRisk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")
    
    risk.status = status_request.status
    if status_request.last_update:
        risk.last_update = status_request.last_update
    if status_request.follow_up_date:
        risk.follow_up_date = status_request.follow_up_date
    
    db.add(risk)
    db.commit()
    db.refresh(risk)
    
    return RiskResponse(
        id=risk.id,
        project_id=risk.project_id,
        risk_no=risk.risk_no,
        risk_category=risk.risk_category,
        risk_name=risk.risk_name,
        description=risk.description,
        probability=risk.probability,
        impact=risk.impact,
        risk_level=risk.risk_level,
        response_strategy=risk.response_strategy,
        response_plan=risk.response_plan,
        owner_id=risk.owner_id,
        owner_name=risk.owner_name,
        status=risk.status,
        follow_up_date=risk.follow_up_date,
        last_update=risk.last_update,
        trigger_condition=risk.trigger_condition,
        is_triggered=risk.is_triggered,
        triggered_date=risk.triggered_date,
        closed_date=risk.closed_date,
        closed_reason=risk.closed_reason,
        created_at=risk.created_at,
        updated_at=risk.updated_at,
    )


@router.put("/pmo/risks/{risk_id}/close", response_model=RiskResponse)
def close_risk(
    *,
    db: Session = Depends(deps.get_db),
    risk_id: int,
    close_request: RiskCloseRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    风险关闭
    """
    risk = db.query(PmoProjectRisk).filter(PmoProjectRisk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")
    
    risk.status = 'CLOSED'
    risk.closed_date = date.today()
    risk.closed_reason = close_request.closed_reason
    
    db.add(risk)
    db.commit()
    db.refresh(risk)
    
    return RiskResponse(
        id=risk.id,
        project_id=risk.project_id,
        risk_no=risk.risk_no,
        risk_category=risk.risk_category,
        risk_name=risk.risk_name,
        description=risk.description,
        probability=risk.probability,
        impact=risk.impact,
        risk_level=risk.risk_level,
        response_strategy=risk.response_strategy,
        response_plan=risk.response_plan,
        owner_id=risk.owner_id,
        owner_name=risk.owner_name,
        status=risk.status,
        follow_up_date=risk.follow_up_date,
        last_update=risk.last_update,
        trigger_condition=risk.trigger_condition,
        is_triggered=risk.is_triggered,
        triggered_date=risk.triggered_date,
        closed_date=risk.closed_date,
        closed_reason=risk.closed_reason,
        created_at=risk.created_at,
        updated_at=risk.updated_at,
    )


# ==================== 项目结项 ====================

@router.post("/pmo/projects/{project_id}/closure", response_model=ClosureResponse, status_code=status.HTTP_201_CREATED)
def create_closure(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    closure_in: ClosureCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    结项申请
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查是否已有结项记录
    existing = db.query(PmoProjectClosure).filter(PmoProjectClosure.project_id == project_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="该项目已有结项记录")
    
    # 计算成本偏差
    cost_variance = None
    if project.budget_amount and project.actual_cost:
        cost_variance = float(project.actual_cost - project.budget_amount)
    
    # 计算工时偏差（从资源分配表统计）
    planned_hours = db.query(func.sum(PmoResourceAllocation.planned_hours)).filter(
        PmoResourceAllocation.project_id == project_id
    ).scalar() or 0
    
    actual_hours = db.query(func.sum(PmoResourceAllocation.actual_hours)).filter(
        PmoResourceAllocation.project_id == project_id
    ).scalar() or 0
    
    hours_variance = actual_hours - planned_hours
    
    # 计算进度偏差
    schedule_variance = None
    if project.planned_end_date and project.actual_end_date:
        schedule_variance = (project.actual_end_date - project.planned_end_date).days
    
    plan_duration = None
    actual_duration = None
    if project.planned_start_date and project.planned_end_date:
        plan_duration = (project.planned_end_date - project.planned_start_date).days
    if project.actual_start_date and project.actual_end_date:
        actual_duration = (project.actual_end_date - project.actual_start_date).days
    
    closure = PmoProjectClosure(
        project_id=project_id,
        acceptance_date=closure_in.acceptance_date,
        acceptance_result=closure_in.acceptance_result,
        acceptance_notes=closure_in.acceptance_notes,
        project_summary=closure_in.project_summary,
        achievement=closure_in.achievement,
        lessons_learned=closure_in.lessons_learned,
        improvement_suggestions=closure_in.improvement_suggestions,
        final_budget=project.budget_amount,
        final_cost=project.actual_cost,
        cost_variance=Decimal(str(cost_variance)) if cost_variance else None,
        final_planned_hours=planned_hours,
        final_actual_hours=actual_hours,
        hours_variance=hours_variance,
        plan_duration=plan_duration,
        actual_duration=actual_duration,
        schedule_variance=schedule_variance,
        quality_score=closure_in.quality_score,
        customer_satisfaction=closure_in.customer_satisfaction,
        status='DRAFT'
    )
    
    db.add(closure)
    db.commit()
    db.refresh(closure)
    
    return ClosureResponse(
        id=closure.id,
        project_id=closure.project_id,
        acceptance_date=closure.acceptance_date,
        acceptance_result=closure.acceptance_result,
        acceptance_notes=closure.acceptance_notes,
        project_summary=closure.project_summary,
        achievement=closure.achievement,
        lessons_learned=closure.lessons_learned,
        improvement_suggestions=closure.improvement_suggestions,
        final_budget=float(closure.final_budget) if closure.final_budget else None,
        final_cost=float(closure.final_cost) if closure.final_cost else None,
        cost_variance=float(closure.cost_variance) if closure.cost_variance else None,
        final_planned_hours=closure.final_planned_hours,
        final_actual_hours=closure.final_actual_hours,
        hours_variance=closure.hours_variance,
        plan_duration=closure.plan_duration,
        actual_duration=closure.actual_duration,
        schedule_variance=closure.schedule_variance,
        quality_score=closure.quality_score,
        customer_satisfaction=closure.customer_satisfaction,
        status=closure.status,
        review_result=closure.review_result,
        review_notes=closure.review_notes,
        reviewed_at=closure.reviewed_at,
        reviewed_by=closure.reviewed_by,
        created_at=closure.created_at,
        updated_at=closure.updated_at,
    )


@router.get("/pmo/projects/{project_id}/closure", response_model=ClosureResponse)
def read_closure(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    结项详情
    """
    closure = db.query(PmoProjectClosure).filter(PmoProjectClosure.project_id == project_id).first()
    if not closure:
        raise HTTPException(status_code=404, detail="结项记录不存在")
    
    return ClosureResponse(
        id=closure.id,
        project_id=closure.project_id,
        acceptance_date=closure.acceptance_date,
        acceptance_result=closure.acceptance_result,
        acceptance_notes=closure.acceptance_notes,
        project_summary=closure.project_summary,
        achievement=closure.achievement,
        lessons_learned=closure.lessons_learned,
        improvement_suggestions=closure.improvement_suggestions,
        final_budget=float(closure.final_budget) if closure.final_budget else None,
        final_cost=float(closure.final_cost) if closure.final_cost else None,
        cost_variance=float(closure.cost_variance) if closure.cost_variance else None,
        final_planned_hours=closure.final_planned_hours,
        final_actual_hours=closure.final_actual_hours,
        hours_variance=closure.hours_variance,
        plan_duration=closure.plan_duration,
        actual_duration=closure.actual_duration,
        schedule_variance=closure.schedule_variance,
        quality_score=closure.quality_score,
        customer_satisfaction=closure.customer_satisfaction,
        status=closure.status,
        review_result=closure.review_result,
        review_notes=closure.review_notes,
        reviewed_at=closure.reviewed_at,
        reviewed_by=closure.reviewed_by,
        created_at=closure.created_at,
        updated_at=closure.updated_at,
    )


@router.put("/pmo/closures/{closure_id}/review", response_model=ClosureResponse)
def review_closure(
    *,
    db: Session = Depends(deps.get_db),
    closure_id: int,
    review_request: ClosureReviewRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    结项评审
    """
    closure = db.query(PmoProjectClosure).filter(PmoProjectClosure.id == closure_id).first()
    if not closure:
        raise HTTPException(status_code=404, detail="结项记录不存在")
    
    closure.status = 'REVIEWED'
    closure.review_result = review_request.review_result
    closure.review_notes = review_request.review_notes
    closure.reviewed_at = datetime.now()
    closure.reviewed_by = current_user.id
    
    db.add(closure)
    db.commit()
    db.refresh(closure)
    
    return ClosureResponse(
        id=closure.id,
        project_id=closure.project_id,
        acceptance_date=closure.acceptance_date,
        acceptance_result=closure.acceptance_result,
        acceptance_notes=closure.acceptance_notes,
        project_summary=closure.project_summary,
        achievement=closure.achievement,
        lessons_learned=closure.lessons_learned,
        improvement_suggestions=closure.improvement_suggestions,
        final_budget=float(closure.final_budget) if closure.final_budget else None,
        final_cost=float(closure.final_cost) if closure.final_cost else None,
        cost_variance=float(closure.cost_variance) if closure.cost_variance else None,
        final_planned_hours=closure.final_planned_hours,
        final_actual_hours=closure.final_actual_hours,
        hours_variance=closure.hours_variance,
        plan_duration=closure.plan_duration,
        actual_duration=closure.actual_duration,
        schedule_variance=closure.schedule_variance,
        quality_score=closure.quality_score,
        customer_satisfaction=closure.customer_satisfaction,
        status=closure.status,
        review_result=closure.review_result,
        review_notes=closure.review_notes,
        reviewed_at=closure.reviewed_at,
        reviewed_by=closure.reviewed_by,
        created_at=closure.created_at,
        updated_at=closure.updated_at,
    )


@router.put("/pmo/closures/{closure_id}/lessons", response_model=ClosureResponse)
def update_closure_lessons(
    *,
    db: Session = Depends(deps.get_db),
    closure_id: int,
    lessons_request: ClosureLessonsRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    经验教训
    """
    closure = db.query(PmoProjectClosure).filter(PmoProjectClosure.id == closure_id).first()
    if not closure:
        raise HTTPException(status_code=404, detail="结项记录不存在")
    
    closure.lessons_learned = lessons_request.lessons_learned
    closure.improvement_suggestions = lessons_request.improvement_suggestions
    
    db.add(closure)
    db.commit()
    db.refresh(closure)
    
    return ClosureResponse(
        id=closure.id,
        project_id=closure.project_id,
        acceptance_date=closure.acceptance_date,
        acceptance_result=closure.acceptance_result,
        acceptance_notes=closure.acceptance_notes,
        project_summary=closure.project_summary,
        achievement=closure.achievement,
        lessons_learned=closure.lessons_learned,
        improvement_suggestions=closure.improvement_suggestions,
        final_budget=float(closure.final_budget) if closure.final_budget else None,
        final_cost=float(closure.final_cost) if closure.final_cost else None,
        cost_variance=float(closure.cost_variance) if closure.cost_variance else None,
        final_planned_hours=closure.final_planned_hours,
        final_actual_hours=closure.final_actual_hours,
        hours_variance=closure.hours_variance,
        plan_duration=closure.plan_duration,
        actual_duration=closure.actual_duration,
        schedule_variance=closure.schedule_variance,
        quality_score=closure.quality_score,
        customer_satisfaction=closure.customer_satisfaction,
        status=closure.status,
        review_result=closure.review_result,
        review_notes=closure.review_notes,
        reviewed_at=closure.reviewed_at,
        reviewed_by=closure.reviewed_by,
        created_at=closure.created_at,
        updated_at=closure.updated_at,
    )


@router.post("/pmo/closures/{closure_id}/archive", response_model=ResponseModel)
def archive_closure(
    *,
    db: Session = Depends(deps.get_db),
    closure_id: int,
    archive_paths: Optional[List[str]] = Query(None, description="归档文件路径列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    文档归档
    """
    closure = db.query(PmoProjectClosure).filter(PmoProjectClosure.id == closure_id).first()
    if not closure:
        raise HTTPException(status_code=404, detail="结项记录不存在")
    
    # 更新归档状态
    closure.status = 'ARCHIVED'
    # 如果有归档路径，可以存储到数据库（需要扩展模型字段）或记录到日志
    
    db.add(closure)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="文档归档成功",
        data={
            "closure_id": closure_id,
            "project_id": closure.project_id,
            "archive_paths": archive_paths or [],
            "archived_at": datetime.now().isoformat()
        }
    )


# ==================== PMO 驾驶舱 ====================

@router.get("/pmo/dashboard", response_model=DashboardResponse)
def get_pmo_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    PMO 驾驶舱数据
    """
    # 统计项目
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.is_active == True).count()
    completed_projects = db.query(Project).filter(Project.stage == 'S9').count()
    
    # 统计延期项目（简化：计划结束日期已过但未完成）
    from datetime import date
    today = date.today()
    delayed_projects = db.query(Project).filter(
        Project.planned_end_date < today,
        Project.stage != 'S9',
        Project.is_active == True
    ).count()
    
    # 统计预算和成本
    budget_result = db.query(func.sum(Project.budget_amount)).scalar() or 0
    cost_result = db.query(func.sum(Project.actual_cost)).scalar() or 0
    
    # 统计风险
    total_risks = db.query(PmoProjectRisk).filter(PmoProjectRisk.status != 'CLOSED').count()
    high_risks = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.risk_level == 'HIGH',
        PmoProjectRisk.status != 'CLOSED'
    ).count()
    critical_risks = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.risk_level == 'CRITICAL',
        PmoProjectRisk.status != 'CLOSED'
    ).count()
    
    # 按状态统计项目
    projects_by_status = {}
    status_counts = db.query(Project.status, func.count(Project.id)).group_by(Project.status).all()
    for status, count in status_counts:
        projects_by_status[status] = count
    
    # 按阶段统计项目
    projects_by_stage = {}
    stage_counts = db.query(Project.stage, func.count(Project.id)).group_by(Project.stage).all()
    for stage, count in stage_counts:
        projects_by_stage[stage] = count
    
    # 最近的风险
    recent_risks = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.status != 'CLOSED'
    ).order_by(desc(PmoProjectRisk.created_at)).limit(10).all()
    
    risk_list = []
    for risk in recent_risks:
        risk_list.append(RiskResponse(
            id=risk.id,
            project_id=risk.project_id,
            risk_no=risk.risk_no,
            risk_category=risk.risk_category,
            risk_name=risk.risk_name,
            description=risk.description,
            probability=risk.probability,
            impact=risk.impact,
            risk_level=risk.risk_level,
            response_strategy=risk.response_strategy,
            response_plan=risk.response_plan,
            owner_id=risk.owner_id,
            owner_name=risk.owner_name,
            status=risk.status,
            follow_up_date=risk.follow_up_date,
            last_update=risk.last_update,
            trigger_condition=risk.trigger_condition,
            is_triggered=risk.is_triggered,
            triggered_date=risk.triggered_date,
            closed_date=risk.closed_date,
            closed_reason=risk.closed_reason,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
        ))
    
    return DashboardResponse(
        summary=DashboardSummary(
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            delayed_projects=delayed_projects,
            total_budget=float(budget_result),
            total_cost=float(cost_result),
            total_risks=total_risks,
            high_risks=high_risks,
            critical_risks=critical_risks
        ),
        projects_by_status=projects_by_status,
        projects_by_stage=projects_by_stage,
        recent_risks=risk_list
    )


@router.get("/pmo/risk-wall", response_model=RiskWallResponse)
def get_risk_wall(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    风险预警墙
    """
    # 统计风险
    total_risks = db.query(PmoProjectRisk).filter(PmoProjectRisk.status != 'CLOSED').count()
    
    # 严重风险
    critical_risks = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.risk_level == 'CRITICAL',
        PmoProjectRisk.status != 'CLOSED'
    ).order_by(desc(PmoProjectRisk.created_at)).all()
    
    # 高风险
    high_risks = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.risk_level == 'HIGH',
        PmoProjectRisk.status != 'CLOSED'
    ).order_by(desc(PmoProjectRisk.created_at)).limit(20).all()
    
    # 按类别统计
    by_category = {}
    category_counts = db.query(
        PmoProjectRisk.risk_category,
        func.count(PmoProjectRisk.id)
    ).filter(
        PmoProjectRisk.status != 'CLOSED'
    ).group_by(PmoProjectRisk.risk_category).all()
    
    for category, count in category_counts:
        by_category[category] = count
    
    # 按项目统计
    by_project = []
    project_risks = db.query(
        PmoProjectRisk.project_id,
        func.count(PmoProjectRisk.id).label('risk_count')
    ).filter(
        PmoProjectRisk.status != 'CLOSED'
    ).group_by(PmoProjectRisk.project_id).order_by(desc('risk_count')).limit(10).all()
    
    for project_id, risk_count in project_risks:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            by_project.append({
                'project_id': project_id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'risk_count': risk_count
            })
    
    critical_list = []
    for risk in critical_risks:
        critical_list.append(RiskResponse(
            id=risk.id,
            project_id=risk.project_id,
            risk_no=risk.risk_no,
            risk_category=risk.risk_category,
            risk_name=risk.risk_name,
            description=risk.description,
            probability=risk.probability,
            impact=risk.impact,
            risk_level=risk.risk_level,
            response_strategy=risk.response_strategy,
            response_plan=risk.response_plan,
            owner_id=risk.owner_id,
            owner_name=risk.owner_name,
            status=risk.status,
            follow_up_date=risk.follow_up_date,
            last_update=risk.last_update,
            trigger_condition=risk.trigger_condition,
            is_triggered=risk.is_triggered,
            triggered_date=risk.triggered_date,
            closed_date=risk.closed_date,
            closed_reason=risk.closed_reason,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
        ))
    
    high_list = []
    for risk in high_risks:
        high_list.append(RiskResponse(
            id=risk.id,
            project_id=risk.project_id,
            risk_no=risk.risk_no,
            risk_category=risk.risk_category,
            risk_name=risk.risk_name,
            description=risk.description,
            probability=risk.probability,
            impact=risk.impact,
            risk_level=risk.risk_level,
            response_strategy=risk.response_strategy,
            response_plan=risk.response_plan,
            owner_id=risk.owner_id,
            owner_name=risk.owner_name,
            status=risk.status,
            follow_up_date=risk.follow_up_date,
            last_update=risk.last_update,
            trigger_condition=risk.trigger_condition,
            is_triggered=risk.is_triggered,
            triggered_date=risk.triggered_date,
            closed_date=risk.closed_date,
            closed_reason=risk.closed_reason,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
        ))
    
    return RiskWallResponse(
        total_risks=total_risks,
        critical_risks=critical_list,
        high_risks=high_list,
        by_category=by_category,
        by_project=by_project
    )


@router.get("/pmo/weekly-report", response_model=WeeklyReportResponse)
def get_weekly_report(
    db: Session = Depends(deps.get_db),
    week_start: Optional[date] = Query(None, description="周开始日期（默认：当前周）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目状态周报
    """
    from datetime import timedelta
    
    # 默认使用当前周
    today = date.today()
    if not week_start:
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
    
    week_end = week_start + timedelta(days=6)
    
    # 统计新项目（本周创建）
    new_projects = db.query(Project).filter(
        Project.created_at >= datetime.combine(week_start, datetime.min.time()),
        Project.created_at <= datetime.combine(week_end, datetime.max.time())
    ).count()
    
    # 统计完成项目（本周完成）
    completed_projects = db.query(Project).filter(
        Project.actual_end_date >= week_start,
        Project.actual_end_date <= week_end,
        Project.stage == 'S9'
    ).count()
    
    # 统计延期项目
    delayed_projects = db.query(Project).filter(
        Project.planned_end_date < today,
        Project.stage != 'S9',
        Project.is_active == True
    ).count()
    
    # 统计新风险
    new_risks = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.created_at >= datetime.combine(week_start, datetime.min.time()),
        PmoProjectRisk.created_at <= datetime.combine(week_end, datetime.max.time())
    ).count()
    
    # 统计解决风险
    resolved_risks = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.closed_date >= week_start,
        PmoProjectRisk.closed_date <= week_end,
        PmoProjectRisk.status == 'CLOSED'
    ).count()
    
    # 项目更新列表（简化：返回本周有更新的项目）
    project_updates = []
    updated_projects = db.query(Project).filter(
        Project.updated_at >= datetime.combine(week_start, datetime.min.time()),
        Project.updated_at <= datetime.combine(week_end, datetime.max.time())
    ).order_by(desc(Project.updated_at)).limit(10).all()
    
    for proj in updated_projects:
        project_updates.append({
            'project_id': proj.id,
            'project_code': proj.project_code,
            'project_name': proj.project_name,
            'stage': proj.stage,
            'status': proj.status,
            'progress': float(proj.progress_pct) if proj.progress_pct else 0.0,
            'updated_at': proj.updated_at
        })
    
    return WeeklyReportResponse(
        report_date=today,
        week_start=week_start,
        week_end=week_end,
        new_projects=new_projects,
        completed_projects=completed_projects,
        delayed_projects=delayed_projects,
        new_risks=new_risks,
        resolved_risks=resolved_risks,
        project_updates=project_updates
    )


@router.get("/pmo/resource-overview", response_model=ResourceOverviewResponse)
def get_resource_overview(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    资源负荷总览
    """
    # 统计资源分配
    total_resources = db.query(User).filter(User.is_active == True).count()
    
    # 统计已分配资源
    allocated_resource_ids = db.query(PmoResourceAllocation.resource_id).filter(
        PmoResourceAllocation.status.in_(['PLANNED', 'ACTIVE'])
    ).distinct().all()
    allocated_resources = len([r[0] for r in allocated_resource_ids])
    
    available_resources = total_resources - allocated_resources
    
    # 统计超负荷资源（从workload模块计算，这里简化处理）
    # TODO: 可以调用workload模块的API或复用其逻辑
    overloaded_resources = 0
    
    # 按部门统计
    from app.models.organization import Department
    by_department = []
    departments = db.query(Department).all()
    
    for dept in departments:
        dept_users = db.query(User).filter(
            User.department == dept.name,
            User.is_active == True
        ).count()
        
        dept_allocated = db.query(PmoResourceAllocation.resource_id).join(
            User, PmoResourceAllocation.resource_id == User.id
        ).filter(
            User.department == dept.name,
            PmoResourceAllocation.status.in_(['PLANNED', 'ACTIVE'])
        ).distinct().count()
        
        by_department.append({
            'department_id': dept.id,
            'department_name': dept.name,
            'total_resources': dept_users,
            'allocated_resources': dept_allocated,
            'available_resources': dept_users - dept_allocated
        })
    
    return ResourceOverviewResponse(
        total_resources=total_resources,
        allocated_resources=allocated_resources,
        available_resources=available_resources,
        overloaded_resources=overloaded_resources,
        by_department=by_department
    )


# ==================== 会议管理 ====================

@router.get("/pmo/meetings", response_model=PaginatedResponse)
def read_meetings(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    meeting_type: Optional[str] = Query(None, description="会议类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（会议名称）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    会议列表
    """
    query = db.query(PmoMeeting)
    
    if project_id:
        query = query.filter(PmoMeeting.project_id == project_id)
    
    if meeting_type:
        query = query.filter(PmoMeeting.meeting_type == meeting_type)
    
    if status:
        query = query.filter(PmoMeeting.status == status)
    
    if keyword:
        query = query.filter(PmoMeeting.meeting_name.like(f"%{keyword}%"))
    
    total = query.count()
    offset = (page - 1) * page_size
    meetings = query.order_by(desc(PmoMeeting.meeting_date), desc(PmoMeeting.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for meeting in meetings:
        items.append(MeetingResponse(
            id=meeting.id,
            project_id=meeting.project_id,
            meeting_type=meeting.meeting_type,
            meeting_name=meeting.meeting_name,
            meeting_date=meeting.meeting_date,
            start_time=meeting.start_time,
            end_time=meeting.end_time,
            location=meeting.location,
            organizer_id=meeting.organizer_id,
            organizer_name=meeting.organizer_name,
            attendees=meeting.attendees if meeting.attendees else [],
            agenda=meeting.agenda,
            minutes=meeting.minutes,
            decisions=meeting.decisions,
            action_items=meeting.action_items if meeting.action_items else [],
            attachments=meeting.attachments if meeting.attachments else [],
            status=meeting.status,
            created_by=meeting.created_by,
            created_at=meeting.created_at,
            updated_at=meeting.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/pmo/meetings", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
def create_meeting(
    *,
    db: Session = Depends(deps.get_db),
    meeting_in: MeetingCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建会议
    """
    organizer_name = None
    if meeting_in.organizer_id:
        organizer = db.query(User).filter(User.id == meeting_in.organizer_id).first()
        organizer_name = organizer.real_name or organizer.username if organizer else None
    elif not meeting_in.organizer_id:
        # 如果没有指定组织者，使用当前用户
        organizer_name = current_user.real_name or current_user.username
    
    meeting = PmoMeeting(
        project_id=meeting_in.project_id,
        meeting_type=meeting_in.meeting_type,
        meeting_name=meeting_in.meeting_name,
        meeting_date=meeting_in.meeting_date,
        start_time=meeting_in.start_time,
        end_time=meeting_in.end_time,
        location=meeting_in.location,
        organizer_id=meeting_in.organizer_id or current_user.id,
        organizer_name=organizer_name,
        attendees=meeting_in.attendees or [],
        agenda=meeting_in.agenda,
        status='SCHEDULED',
        created_by=current_user.id
    )
    
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    
    return MeetingResponse(
        id=meeting.id,
        project_id=meeting.project_id,
        meeting_type=meeting.meeting_type,
        meeting_name=meeting.meeting_name,
        meeting_date=meeting.meeting_date,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        location=meeting.location,
        organizer_id=meeting.organizer_id,
        organizer_name=meeting.organizer_name,
        attendees=meeting.attendees if meeting.attendees else [],
        agenda=meeting.agenda,
        minutes=meeting.minutes,
        decisions=meeting.decisions,
        action_items=meeting.action_items if meeting.action_items else [],
        attachments=meeting.attachments if meeting.attachments else [],
        status=meeting.status,
        created_by=meeting.created_by,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )


@router.get("/pmo/meetings/{meeting_id}", response_model=MeetingResponse)
def read_meeting(
    *,
    db: Session = Depends(deps.get_db),
    meeting_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    会议详情
    """
    meeting = db.query(PmoMeeting).filter(PmoMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")
    
    return MeetingResponse(
        id=meeting.id,
        project_id=meeting.project_id,
        meeting_type=meeting.meeting_type,
        meeting_name=meeting.meeting_name,
        meeting_date=meeting.meeting_date,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        location=meeting.location,
        organizer_id=meeting.organizer_id,
        organizer_name=meeting.organizer_name,
        attendees=meeting.attendees if meeting.attendees else [],
        agenda=meeting.agenda,
        minutes=meeting.minutes,
        decisions=meeting.decisions,
        action_items=meeting.action_items if meeting.action_items else [],
        attachments=meeting.attachments if meeting.attachments else [],
        status=meeting.status,
        created_by=meeting.created_by,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )


@router.put("/pmo/meetings/{meeting_id}", response_model=MeetingResponse)
def update_meeting(
    *,
    db: Session = Depends(deps.get_db),
    meeting_id: int,
    meeting_in: MeetingUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新会议
    """
    meeting = db.query(PmoMeeting).filter(PmoMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")
    
    update_data = meeting_in.model_dump(exclude_unset=True)
    
    # 如果更新了组织者，更新组织者名称
    if 'organizer_id' in update_data and update_data['organizer_id']:
        organizer = db.query(User).filter(User.id == update_data['organizer_id']).first()
        if organizer:
            update_data['organizer_name'] = organizer.real_name or organizer.username
    
    for field, value in update_data.items():
        setattr(meeting, field, value)
    
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    
    return read_meeting(db=db, meeting_id=meeting_id, current_user=current_user)


@router.put("/pmo/meetings/{meeting_id}/minutes", response_model=MeetingResponse)
def update_meeting_minutes(
    *,
    db: Session = Depends(deps.get_db),
    meeting_id: int,
    minutes_request: MeetingMinutesRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    记录会议纪要
    """
    meeting = db.query(PmoMeeting).filter(PmoMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")
    
    meeting.minutes = minutes_request.minutes
    meeting.decisions = minutes_request.decisions
    meeting.action_items = minutes_request.action_items or []
    meeting.status = 'COMPLETED'
    
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    
    return read_meeting(db=db, meeting_id=meeting_id, current_user=current_user)


@router.get("/pmo/meetings/{meeting_id}/actions", response_model=List[Dict[str, Any]])
def get_meeting_actions(
    *,
    db: Session = Depends(deps.get_db),
    meeting_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    会议待办跟踪
    """
    meeting = db.query(PmoMeeting).filter(PmoMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")
    
    return meeting.action_items if meeting.action_items else []

