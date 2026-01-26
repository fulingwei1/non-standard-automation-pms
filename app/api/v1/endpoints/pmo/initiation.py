# -*- coding: utf-8 -*-
"""
立项管理 - 自动生成
从 pmo.py 拆分
"""

# -*- coding: utf-8 -*-
"""
PMO 项目管理部 API endpoints
包含：立项管理、项目阶段门管理、风险管理、项目结项管理、PMO驾驶舱
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.pmo import (
    PmoMeeting,
    PmoProjectClosure,
    PmoProjectInitiation,
    PmoProjectPhase,
    PmoProjectRisk,
    PmoResourceAllocation,
)
from app.models.project import Customer, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.pmo import (
    ClosureCreate,
    ClosureLessonsRequest,
    ClosureResponse,
    ClosureReviewRequest,
    DashboardResponse,
    DashboardSummary,
    InitiationApproveRequest,
    InitiationCreate,
    InitiationRejectRequest,
    InitiationResponse,
    InitiationUpdate,
    MeetingCreate,
    MeetingMinutesRequest,
    MeetingResponse,
    MeetingUpdate,
    PhaseAdvanceRequest,
    PhaseEntryCheckRequest,
    PhaseExitCheckRequest,
    PhaseResponse,
    PhaseReviewRequest,
    ResourceOverviewResponse,
    RiskAssessRequest,
    RiskCloseRequest,
    RiskCreate,
    RiskResponse,
    RiskResponseRequest,
    RiskStatusUpdateRequest,
    RiskWallResponse,
    WeeklyReportResponse,
)

# This module is included into `app.api.v1.endpoints.pmo.router` without an
# additional prefix. Decorators below already contain `/pmo/...` paths, so we
# must NOT set a router-level prefix here (otherwise paths become duplicated and
# clients hit 404).
router = APIRouter(tags=["pmo-initiation"])

# 使用统一的编码生成工具
from app.utils.domain_codes import pmo as pmo_codes

generate_initiation_no = pmo_codes.generate_initiation_no
generate_risk_no = pmo_codes.generate_risk_no

# 共 7 个路由

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


