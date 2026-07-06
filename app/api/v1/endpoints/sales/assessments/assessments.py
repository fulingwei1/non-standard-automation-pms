# -*- coding: utf-8 -*-
"""
技术评估核心管理 API endpoints

包含技术评估的申请、执行、查询等核心端点
"""

from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import AssessmentSourceTypeEnum, AssessmentStatusEnum
from app.models.presale import PresaleSupportTicket
from app.models.sales import AssessmentTemplate, Lead, Opportunity, TechnicalAssessment
from app.models.sales.operation_log import SalesOperationType
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import (
    TechnicalAssessmentApplyRequest,
    TechnicalAssessmentEvaluateRequest,
    TechnicalAssessmentResponse,
)
from app.services.sales.lead_operation_audit import lead_audit_value, log_lead_operation
from app.services.sales.opportunity_operation_audit import (
    log_opportunity_operation,
    opportunity_audit_value,
)
from app.services.ai_assessment_service import AIAssessmentService
from app.services.technical_assessment_service import TechnicalAssessmentService
from app.utils.db_helpers import get_or_404

router = APIRouter()


OPEN_ASSESSMENT_STATUSES = {
    AssessmentStatusEnum.PENDING.value,
    AssessmentStatusEnum.IN_PROGRESS.value,
}


def _find_open_assessment(
    db: Session,
    source_type: str,
    source_id: int,
    assessment_id: Optional[int] = None,
    presale_ticket_id: Optional[int] = None,
) -> Optional[TechnicalAssessment]:
    query = db.query(TechnicalAssessment).filter(
        TechnicalAssessment.source_type == source_type,
        TechnicalAssessment.source_id == source_id,
        TechnicalAssessment.status.in_(OPEN_ASSESSMENT_STATUSES),
    )
    if assessment_id:
        linked_assessment = query.filter(TechnicalAssessment.id == assessment_id).first()
        if linked_assessment:
            linked_ticket_id = linked_assessment.presale_ticket_id
            if not (presale_ticket_id and linked_ticket_id and linked_ticket_id != presale_ticket_id):
                return linked_assessment

    if presale_ticket_id:
        ticket_assessment = (
            query.filter(TechnicalAssessment.presale_ticket_id == presale_ticket_id)
            .order_by(desc(TechnicalAssessment.created_at))
            .first()
        )
        if ticket_assessment:
            return ticket_assessment

        unbound_assessment = (
            query.filter(TechnicalAssessment.presale_ticket_id.is_(None))
            .order_by(desc(TechnicalAssessment.created_at))
            .first()
        )
        if unbound_assessment:
            return unbound_assessment

        return None

    return query.order_by(desc(TechnicalAssessment.created_at)).first()


def _get_presale_ticket_for_source(
    db: Session,
    *,
    source_type: str,
    source_id: int,
    presale_ticket_id: Optional[int],
) -> Optional[PresaleSupportTicket]:
    if not presale_ticket_id:
        return None

    ticket = db.query(PresaleSupportTicket).filter(PresaleSupportTicket.id == presale_ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="售前工单不存在")

    if source_type == AssessmentSourceTypeEnum.LEAD.value and ticket.lead_id != source_id:
        raise HTTPException(status_code=400, detail="售前工单与线索不匹配")
    if (
        source_type == AssessmentSourceTypeEnum.OPPORTUNITY.value
        and ticket.opportunity_id != source_id
    ):
        raise HTTPException(status_code=400, detail="售前工单与商机不匹配")

    return ticket


def _validate_assessment_template(
    db: Session,
    template_id: Optional[int],
) -> Optional[AssessmentTemplate]:
    if not template_id:
        return None

    template = db.query(AssessmentTemplate).filter(AssessmentTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="评估模板不存在")
    if not template.is_active:
        raise HTTPException(status_code=400, detail="评估模板已停用")
    return template


def _bind_presale_ticket(
    ticket: Optional[PresaleSupportTicket],
    assessment: TechnicalAssessment,
) -> None:
    if not ticket:
        return

    assessment.presale_ticket_id = ticket.id
    ticket.current_assessment_id = assessment.id
    ticket.assessment_status = assessment.status


def _assessment_response(
    db: Session,
    assessment: TechnicalAssessment,
) -> TechnicalAssessmentResponse:
    evaluator_name = None
    if assessment.evaluator_id:
        evaluator = db.query(User).filter(User.id == assessment.evaluator_id).first()
        evaluator_name = evaluator.real_name if evaluator else None

    return TechnicalAssessmentResponse(
        id=assessment.id,
        source_type=assessment.source_type,
        source_id=assessment.source_id,
        evaluator_id=assessment.evaluator_id,
        status=assessment.status,
        total_score=assessment.total_score,
        dimension_scores=assessment.dimension_scores,
        veto_triggered=assessment.veto_triggered,
        veto_rules=assessment.veto_rules,
        decision=assessment.decision,
        risks=assessment.risks,
        similar_cases=assessment.similar_cases,
        ai_analysis=assessment.ai_analysis,
        conditions=assessment.conditions,
        evaluated_at=assessment.evaluated_at,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        evaluator_name=evaluator_name,
        presale_ticket_id=assessment.presale_ticket_id,
        template_id=assessment.template_id,
        version_no=assessment.version_no,
        item_scores=assessment.item_scores,
        auto_generated=bool(getattr(assessment, "auto_generated", False)),
    )


def _source_audit_value(
    db: Session,
    assessment: TechnicalAssessment,
) -> dict[str, Any]:
    if assessment.source_type == AssessmentSourceTypeEnum.LEAD.value:
        lead = get_or_404(db, Lead, assessment.source_id, detail="线索不存在")
        return lead_audit_value(lead)
    if assessment.source_type == AssessmentSourceTypeEnum.OPPORTUNITY.value:
        opportunity = get_or_404(db, Opportunity, assessment.source_id, detail="商机不存在")
        return opportunity_audit_value(opportunity)
    return {}


def _log_assessment_source_operation(
    db: Session,
    assessment: TechnicalAssessment,
    operation_type: str,
    current_user: User,
    *,
    old_value: dict[str, Any],
    operation_desc: str,
    remark: str | None = None,
) -> None:
    if assessment.source_type == AssessmentSourceTypeEnum.LEAD.value:
        lead = get_or_404(db, Lead, assessment.source_id, detail="线索不存在")
        log_lead_operation(
            db,
            lead,
            operation_type,
            current_user,
            old_value=old_value,
            new_value=lead_audit_value(lead),
            operation_desc=operation_desc,
            remark=remark,
        )
        return

    if assessment.source_type == AssessmentSourceTypeEnum.OPPORTUNITY.value:
        opportunity = get_or_404(db, Opportunity, assessment.source_id, detail="商机不存在")
        log_opportunity_operation(
            db,
            opportunity,
            operation_type,
            current_user,
            old_value=old_value,
            new_value=opportunity_audit_value(opportunity),
            operation_desc=operation_desc,
            remark=remark,
        )


def _get_or_create_open_assessment(
    db: Session,
    *,
    source_type: str,
    source_id: int,
    evaluator_id: int,
    existing_assessment_id: Optional[int] = None,
    presale_ticket_id: Optional[int] = None,
    template_id: Optional[int] = None,
) -> TechnicalAssessment:
    assessment = _find_open_assessment(
        db,
        source_type=source_type,
        source_id=source_id,
        assessment_id=existing_assessment_id,
        presale_ticket_id=presale_ticket_id,
    )
    if assessment:
        assessment.evaluator_id = evaluator_id
        if presale_ticket_id:
            assessment.presale_ticket_id = presale_ticket_id
        if template_id:
            assessment.template_id = template_id
        return assessment

    assessment = TechnicalAssessment(
        source_type=source_type,
        source_id=source_id,
        evaluator_id=evaluator_id,
        status=AssessmentStatusEnum.PENDING.value,
        presale_ticket_id=presale_ticket_id,
        template_id=template_id,
    )
    db.add(assessment)
    db.flush()
    return assessment


@router.post("/leads/{lead_id}/assessments/apply", response_model=ResponseModel, status_code=201)
def apply_lead_assessment(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    request: TechnicalAssessmentApplyRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """申请技术评估（线索）"""
    lead = get_or_404(db, Lead, lead_id, detail="线索不存在")
    old_value = lead_audit_value(lead)
    ticket = _get_presale_ticket_for_source(
        db,
        source_type=AssessmentSourceTypeEnum.LEAD.value,
        source_id=lead_id,
        presale_ticket_id=request.presale_ticket_id,
    )
    _validate_assessment_template(db, request.template_id)

    assessment = _get_or_create_open_assessment(
        db,
        source_type=AssessmentSourceTypeEnum.LEAD.value,
        source_id=lead_id,
        evaluator_id=request.evaluator_id or current_user.id,
        existing_assessment_id=lead.assessment_id,
        presale_ticket_id=request.presale_ticket_id,
        template_id=request.template_id,
    )
    _bind_presale_ticket(ticket, assessment)

    # 更新线索
    lead.assessment_id = assessment.id
    lead.assessment_status = assessment.status

    db.flush()
    log_lead_operation(
        db,
        lead,
        SalesOperationType.UPDATE,
        current_user,
        old_value=old_value,
        new_value=lead_audit_value(lead),
        operation_desc="申请线索技术评估",
        remark=str(assessment.id),
    )
    db.commit()

    return ResponseModel(
        message="技术评估申请已提交",
        data={
            "assessment_id": assessment.id,
            "presale_ticket_id": assessment.presale_ticket_id,
            "template_id": assessment.template_id,
        },
    )


@router.post(
    "/opportunities/{opp_id}/assessments/apply", response_model=ResponseModel, status_code=201
)
def apply_opportunity_assessment(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    request: TechnicalAssessmentApplyRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """申请技术评估（商机）"""
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")
    old_value = opportunity_audit_value(opportunity)
    ticket = _get_presale_ticket_for_source(
        db,
        source_type=AssessmentSourceTypeEnum.OPPORTUNITY.value,
        source_id=opp_id,
        presale_ticket_id=request.presale_ticket_id,
    )
    _validate_assessment_template(db, request.template_id)

    assessment = _get_or_create_open_assessment(
        db,
        source_type=AssessmentSourceTypeEnum.OPPORTUNITY.value,
        source_id=opp_id,
        evaluator_id=request.evaluator_id or current_user.id,
        existing_assessment_id=opportunity.assessment_id,
        presale_ticket_id=request.presale_ticket_id,
        template_id=request.template_id,
    )
    _bind_presale_ticket(ticket, assessment)

    # 更新商机
    opportunity.assessment_id = assessment.id
    opportunity.assessment_status = assessment.status

    db.flush()
    log_opportunity_operation(
        db,
        opportunity,
        SalesOperationType.UPDATE,
        current_user,
        old_value=old_value,
        new_value=opportunity_audit_value(opportunity),
        operation_desc="申请商机技术评估",
        remark=str(assessment.id),
    )
    db.commit()

    return ResponseModel(
        message="技术评估申请已提交",
        data={
            "assessment_id": assessment.id,
            "presale_ticket_id": assessment.presale_ticket_id,
            "template_id": assessment.template_id,
        },
    )


@router.post(
    "/assessments/{assessment_id}/evaluate",
    response_model=TechnicalAssessmentResponse,
    status_code=200,
)
async def evaluate_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    request: TechnicalAssessmentEvaluateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """执行技术评估"""
    assessment = get_or_404(db, TechnicalAssessment, assessment_id, detail="技术评估不存在")
    old_source_value = _source_audit_value(db, assessment)

    if assessment.status != AssessmentStatusEnum.PENDING.value:
        raise HTTPException(status_code=400, detail="评估状态不正确")
    if request.template_id:
        _validate_assessment_template(db, request.template_id)
        assessment.template_id = request.template_id
        db.flush()

    # 可选：AI分析
    ai_analysis = None
    if request.enable_ai:
        ai_service = AIAssessmentService()
        if ai_service.is_available():
            ai_analysis = await ai_service.analyze_requirement(request.requirement_data)

    # 执行评估
    service = TechnicalAssessmentService(db)
    assessment = service.evaluate(
        assessment.source_type,
        assessment.source_id,
        current_user.id,
        request.requirement_data,
        ai_analysis=ai_analysis,
        assessment_id=assessment.id,
    )

    db.flush()
    operation_desc = (
        "执行线索技术评估"
        if assessment.source_type == AssessmentSourceTypeEnum.LEAD.value
        else "执行商机技术评估"
    )
    _log_assessment_source_operation(
        db,
        assessment,
        SalesOperationType.UPDATE,
        current_user,
        old_value=old_source_value,
        operation_desc=operation_desc,
        remark=assessment.decision,
    )
    db.commit()

    db.refresh(assessment)

    return _assessment_response(db, assessment)


@router.get("/leads/{lead_id}/assessments", response_model=List[TechnicalAssessmentResponse])
def get_lead_assessments(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取线索的技术评估列表"""
    assessments = (
        db.query(TechnicalAssessment)
        .filter(
            and_(
                TechnicalAssessment.source_type == AssessmentSourceTypeEnum.LEAD.value,
                TechnicalAssessment.source_id == lead_id,
            )
        )
        .order_by(desc(TechnicalAssessment.created_at))
        .all()
    )

    return [_assessment_response(db, assessment) for assessment in assessments]


@router.get("/opportunities/{opp_id}/assessments", response_model=List[TechnicalAssessmentResponse])
def get_opportunity_assessments(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取商机的技术评估列表"""
    assessments = (
        db.query(TechnicalAssessment)
        .filter(
            and_(
                TechnicalAssessment.source_type == AssessmentSourceTypeEnum.OPPORTUNITY.value,
                TechnicalAssessment.source_id == opp_id,
            )
        )
        .order_by(desc(TechnicalAssessment.created_at))
        .all()
    )

    return [_assessment_response(db, assessment) for assessment in assessments]


@router.get("/assessments/{assessment_id}", response_model=TechnicalAssessmentResponse)
def get_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取技术评估详情"""
    assessment = get_or_404(db, TechnicalAssessment, assessment_id, detail="技术评估不存在")

    return _assessment_response(db, assessment)
