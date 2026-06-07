# -*- coding: utf-8 -*-
"""售前工单与技术评估闭环的共享逻辑。"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.enums import AssessmentStatusEnum
from app.models.presale import PresaleSupportTicket
from app.models.sales import TechnicalAssessment
from app.models.user import User


def _load_assessment(db: Session, assessment_id: Optional[int]) -> Optional[TechnicalAssessment]:
    if not assessment_id:
        return None
    return (
        db.query(TechnicalAssessment)
        .filter(TechnicalAssessment.id == assessment_id)
        .first()
    )


def _can_use_for_ticket(
    assessment: Optional[TechnicalAssessment],
    ticket: Optional[PresaleSupportTicket],
) -> bool:
    if assessment is None:
        return False
    if ticket is None:
        return True
    linked_ticket_id = getattr(assessment, "presale_ticket_id", None)
    return linked_ticket_id is None or linked_ticket_id == ticket.id


def _find_reusable_assessment(
    *,
    db: Session,
    source_type: str,
    source_id: int,
    ticket: Optional[PresaleSupportTicket],
    source_assessment_id: Optional[int],
) -> Optional[TechnicalAssessment]:
    if ticket:
        ticket_assessment = _load_assessment(db, ticket.current_assessment_id)
        if _can_use_for_ticket(ticket_assessment, ticket):
            return ticket_assessment

    source_assessment = _load_assessment(db, source_assessment_id)
    if _can_use_for_ticket(source_assessment, ticket):
        return source_assessment

    base_query = db.query(TechnicalAssessment).filter(
        TechnicalAssessment.source_type == source_type,
        TechnicalAssessment.source_id == source_id,
    )

    if ticket:
        bound_assessment = (
            base_query.filter(TechnicalAssessment.presale_ticket_id == ticket.id)
            .order_by(TechnicalAssessment.id.desc())
            .first()
        )
        if bound_assessment:
            return bound_assessment

        return (
            base_query.filter(TechnicalAssessment.presale_ticket_id.is_(None))
            .order_by(TechnicalAssessment.id.desc())
            .first()
        )

    return base_query.order_by(TechnicalAssessment.id.desc()).first()


def complete_presale_source_assessment(
    *,
    db: Session,
    source_type: str,
    source_id: int,
    current_user: User,
    ticket: Optional[PresaleSupportTicket] = None,
    source_assessment_id: Optional[int] = None,
) -> TechnicalAssessment:
    """补齐售前来源对象的技术评估，避免串用其它工单的评估记录。"""
    assessment = _find_reusable_assessment(
        db=db,
        source_type=source_type,
        source_id=source_id,
        ticket=ticket,
        source_assessment_id=source_assessment_id,
    )

    if assessment is None:
        assessment = TechnicalAssessment(
            source_type=source_type,
            source_id=source_id,
            evaluator_id=current_user.id,
            status=AssessmentStatusEnum.COMPLETED.value,
            decision="推荐立项",
            evaluated_at=datetime.now(),
            presale_ticket_id=ticket.id if ticket else None,
        )
        db.add(assessment)
        db.flush()
    else:
        assessment.source_type = source_type
        assessment.source_id = source_id
        assessment.status = AssessmentStatusEnum.COMPLETED.value
        assessment.decision = assessment.decision or "推荐立项"
        assessment.evaluator_id = assessment.evaluator_id or current_user.id
        assessment.evaluated_at = assessment.evaluated_at or datetime.now()
        if ticket and not assessment.presale_ticket_id:
            assessment.presale_ticket_id = ticket.id

    if ticket:
        ticket.assessment_status = AssessmentStatusEnum.COMPLETED.value
        ticket.current_assessment_id = assessment.id

    return assessment
