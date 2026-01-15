# -*- coding: utf-8 -*-
"""
风险管理 - 自动生成
从 pmo.py 拆分
"""

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



from fastapi import APIRouter

router = APIRouter(
    prefix="/pmo/risks",
    tags=["risks"]
)

# 共 6 个路由

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



