# -*- coding: utf-8 -*-
"""
售前工单管理 - 业务操作
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import AssessmentSourceTypeEnum, AssessmentStatusEnum
from app.models.presale import PresaleSupportTicket, PresaleTicketDeliverable, PresaleTicketProgress
from app.models.sales import Lead, Opportunity, TechnicalAssessment
from app.models.user import User
from app.schemas.presale import (
    DeliverableCreate,
    DeliverableReviewRequest,
    DeliverableResponse,
    TicketAcceptRequest,
    TicketCompleteRequest,
    TicketProgressUpdate,
    TicketRatingRequest,
    TicketResponse,
)
from app.services.presale_assessment_completion import complete_presale_source_assessment
from app.utils.db_helpers import get_or_404, save_obj

from .crud import read_ticket

router = APIRouter()


def _complete_opportunity_assessment_for_ticket(
    *,
    db: Session,
    ticket: PresaleSupportTicket,
    opportunity: Opportunity,
    current_user: User,
) -> TechnicalAssessment:
    """补齐商机关联售前工单的技术评估闭环。"""
    assessment = complete_presale_source_assessment(
        db=db,
        source_type=AssessmentSourceTypeEnum.OPPORTUNITY.value,
        source_id=opportunity.id,
        current_user=current_user,
        ticket=ticket,
        source_assessment_id=opportunity.assessment_id,
    )

    opportunity.assessment_id = assessment.id
    opportunity.assessment_status = AssessmentStatusEnum.COMPLETED.value
    opportunity.updated_by = current_user.id
    return assessment


def _complete_lead_assessment_for_ticket(
    *,
    db: Session,
    ticket: PresaleSupportTicket,
    lead: Lead,
    current_user: User,
) -> TechnicalAssessment:
    """补齐线索关联售前工单的技术评估闭环。"""
    assessment = complete_presale_source_assessment(
        db=db,
        source_type=AssessmentSourceTypeEnum.LEAD.value,
        source_id=lead.id,
        current_user=current_user,
        ticket=ticket,
        source_assessment_id=lead.assessment_id,
    )

    lead.assessment_id = assessment.id
    lead.assessment_status = AssessmentStatusEnum.COMPLETED.value
    return assessment


@router.put("/{ticket_id}/accept", response_model=TicketResponse)
def accept_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    accept_request: TicketAcceptRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    接单确认
    """
    ticket = get_or_404(db, PresaleSupportTicket, ticket_id, detail="工单不存在")

    if ticket.status != "PENDING":
        raise HTTPException(status_code=400, detail="只有待处理状态的工单才能接单")

    assignee_id = accept_request.assignee_id or current_user.id
    assignee = get_or_404(db, User, assignee_id, detail="处理人不存在")

    ticket.assignee_id = assignee_id
    ticket.assignee_name = assignee.real_name or assignee.username
    ticket.accept_time = datetime.now()
    ticket.status = "ACCEPTED"

    save_obj(db, ticket)

    return read_ticket(db=db, ticket_id=ticket_id, current_user=current_user)


@router.put("/{ticket_id}/progress", response_model=TicketResponse)
def update_ticket_progress(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    progress_request: TicketProgressUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新进度
    """
    ticket = get_or_404(db, PresaleSupportTicket, ticket_id, detail="工单不存在")

    if ticket.status not in ["ACCEPTED", "IN_PROGRESS"]:
        raise HTTPException(status_code=400, detail="只有已接单或进行中的工单才能更新进度")

    ticket.status = "IN_PROGRESS"

    # 记录进度
    progress = PresaleTicketProgress(
        ticket_id=ticket_id,
        progress_type="PROGRESS",
        content=progress_request.progress_note,
        progress_percent=progress_request.progress_percent,
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        created_at=datetime.now(),
    )
    db.add(progress)

    save_obj(db, ticket)

    return read_ticket(db=db, ticket_id=ticket_id, current_user=current_user)


@router.post(
    "/{ticket_id}/deliverables",
    response_model=DeliverableResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deliverable(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    deliverable_in: DeliverableCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交交付物
    """
    get_or_404(db, PresaleSupportTicket, ticket_id, detail="工单不存在")

    deliverable = PresaleTicketDeliverable(
        ticket_id=ticket_id,
        name=deliverable_in.deliverable_name,
        file_type=deliverable_in.deliverable_type,
        file_path=deliverable_in.file_path or deliverable_in.file_url,
        created_by=current_user.id,
    )

    save_obj(db, deliverable)

    return DeliverableResponse(
        id=deliverable.id,
        ticket_id=deliverable.ticket_id,
        deliverable_name=deliverable.name,
        deliverable_type=deliverable.file_type or deliverable_in.deliverable_type,
        file_path=deliverable.file_path,
        file_url=deliverable_in.file_url,
        description=deliverable_in.description,
        status=deliverable.status,
        created_at=deliverable.created_at,
        updated_at=deliverable.updated_at,
    )


@router.put(
    "/{ticket_id}/deliverables/{deliverable_id}/review",
    response_model=DeliverableResponse,
)
def review_deliverable(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    deliverable_id: int,
    review_in: DeliverableReviewRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审核交付物
    """
    deliverable = (
        db.query(PresaleTicketDeliverable)
        .filter(
            PresaleTicketDeliverable.id == deliverable_id,
            PresaleTicketDeliverable.ticket_id == ticket_id,
        )
        .first()
    )
    if not deliverable:
        raise HTTPException(status_code=404, detail="交付物不存在")

    review_status = review_in.review_status.upper()
    if review_status not in {"APPROVED", "REJECTED"}:
        raise HTTPException(status_code=400, detail="审核结果仅支持 APPROVED/REJECTED")

    deliverable.status = review_status
    deliverable.reviewer_id = current_user.id
    deliverable.review_time = datetime.now()
    deliverable.review_comment = review_in.review_comment

    save_obj(db, deliverable)

    return DeliverableResponse(
        id=deliverable.id,
        ticket_id=deliverable.ticket_id,
        deliverable_name=deliverable.name,
        deliverable_type=deliverable.file_type,
        file_path=deliverable.file_path,
        file_url=deliverable.file_path,
        status=deliverable.status,
        reviewer_id=deliverable.reviewer_id,
        review_time=deliverable.review_time,
        review_comment=deliverable.review_comment,
        created_at=deliverable.created_at,
        updated_at=deliverable.updated_at,
    )


@router.put("/{ticket_id}/complete", response_model=TicketResponse)
def complete_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    complete_request: Optional[TicketCompleteRequest] = None,
    actual_hours: Optional[float] = Query(None, description="实际工时（兼容旧查询参数）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成工单

    兼容两种调用方式：
    - PUT /complete?actual_hours=8
    - PUT /complete {"actual_hours": 8}
    """
    ticket = get_or_404(db, PresaleSupportTicket, ticket_id, detail="工单不存在")

    ticket.status = "COMPLETED"
    ticket.complete_time = datetime.now()

    resolved_actual_hours = actual_hours
    if complete_request and complete_request.actual_hours is not None:
        resolved_actual_hours = complete_request.actual_hours

    if resolved_actual_hours is not None:
        ticket.actual_hours = Decimal(str(resolved_actual_hours))

    completion_note = "工单已完成"
    if complete_request and complete_request.completion_note:
        completion_note = complete_request.completion_note.strip() or completion_note

    progress = PresaleTicketProgress(
        ticket_id=ticket_id,
        progress_type="COMPLETE",
        content=completion_note,
        progress_percent=100,
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        created_at=datetime.now(),
    )
    db.add(progress)

    if ticket.opportunity_id:
        opportunity = db.query(Opportunity).filter(Opportunity.id == ticket.opportunity_id).first()
        if opportunity:
            _complete_opportunity_assessment_for_ticket(
                db=db,
                ticket=ticket,
                opportunity=opportunity,
                current_user=current_user,
            )
            db.add(opportunity)
    elif ticket.lead_id:
        lead = db.query(Lead).filter(Lead.id == ticket.lead_id).first()
        if lead:
            _complete_lead_assessment_for_ticket(
                db=db,
                ticket=ticket,
                lead=lead,
                current_user=current_user,
            )
            db.add(lead)
    else:
        ticket.assessment_status = AssessmentStatusEnum.COMPLETED.value

    save_obj(db, ticket)

    return read_ticket(db=db, ticket_id=ticket_id, current_user=current_user)


@router.put("/{ticket_id}/rating", response_model=TicketResponse)
def rate_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    rating_request: TicketRatingRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    满意度评价
    """
    ticket = get_or_404(db, PresaleSupportTicket, ticket_id, detail="工单不存在")

    if ticket.applicant_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有申请人才能评价")

    ticket.satisfaction_score = rating_request.satisfaction_score
    ticket.feedback = rating_request.feedback

    save_obj(db, ticket)

    return read_ticket(db=db, ticket_id=ticket_id, current_user=current_user)
