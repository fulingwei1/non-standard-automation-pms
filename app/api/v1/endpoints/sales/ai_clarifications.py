# -*- coding: utf-8 -*-
"""
需求管理 - AI澄清管理

包含AI澄清的CRUD操作
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import AssessmentSourceTypeEnum
from app.models.sales import AIClarification, Lead, Opportunity
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import (
    AIClarificationCreate,
    AIClarificationResponse,
    AIClarificationUpdate,
)

router = APIRouter()


@router.get("/ai-clarifications", response_model=PaginatedResponse[AIClarificationResponse])
def list_ai_clarifications(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_type: Optional[str] = Query(None, description="来源类型：LEAD/OPPORTUNITY"),
    source_id: Optional[int] = Query(None, description="来源ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取AI澄清列表
    """
    query = db.query(AIClarification)

    if source_type:
        query = query.filter(AIClarification.source_type == source_type)
    if source_id:
        query = query.filter(AIClarification.source_id == source_id)

    total = query.count()
    clarifications = query.order_by(
        desc(AIClarification.source_type),
        desc(AIClarification.source_id),
        desc(AIClarification.round)
    ).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for clarification in clarifications:
        items.append(AIClarificationResponse(
            id=clarification.id,
            source_type=clarification.source_type,
            source_id=clarification.source_id,
            round=clarification.round,
            questions=clarification.questions,
            answers=clarification.answers,
            created_at=clarification.created_at,
            updated_at=clarification.updated_at
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/leads/{lead_id}/ai-clarifications", response_model=AIClarificationResponse, status_code=201)
def create_ai_clarification_for_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    clarification_in: AIClarificationCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    为线索创建AI澄清
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    # 获取当前最大轮次
    max_round = db.query(func.max(AIClarification.round)).filter(
        and_(
            AIClarification.source_type == AssessmentSourceTypeEnum.LEAD.value,
            AIClarification.source_id == lead_id
        )
    ).scalar() or 0

    clarification = AIClarification(
        source_type=AssessmentSourceTypeEnum.LEAD.value,
        source_id=lead_id,
        round=max_round + 1,
        questions=clarification_in.questions,
        answers=clarification_in.answers
    )

    db.add(clarification)
    db.commit()
    db.refresh(clarification)

    return AIClarificationResponse(
        id=clarification.id,
        source_type=clarification.source_type,
        source_id=clarification.source_id,
        round=clarification.round,
        questions=clarification.questions,
        answers=clarification.answers,
        created_at=clarification.created_at,
        updated_at=clarification.updated_at
    )


@router.post("/opportunities/{opp_id}/ai-clarifications", response_model=AIClarificationResponse, status_code=201)
def create_ai_clarification_for_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    clarification_in: AIClarificationCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    为商机创建AI澄清
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    # 获取当前最大轮次
    max_round = db.query(func.max(AIClarification.round)).filter(
        and_(
            AIClarification.source_type == AssessmentSourceTypeEnum.OPPORTUNITY.value,
            AIClarification.source_id == opp_id
        )
    ).scalar() or 0

    clarification = AIClarification(
        source_type=AssessmentSourceTypeEnum.OPPORTUNITY.value,
        source_id=opp_id,
        round=max_round + 1,
        questions=clarification_in.questions,
        answers=clarification_in.answers
    )

    db.add(clarification)
    db.commit()
    db.refresh(clarification)

    return AIClarificationResponse(
        id=clarification.id,
        source_type=clarification.source_type,
        source_id=clarification.source_id,
        round=clarification.round,
        questions=clarification.questions,
        answers=clarification.answers,
        created_at=clarification.created_at,
        updated_at=clarification.updated_at
    )


@router.put("/ai-clarifications/{clarification_id}", response_model=AIClarificationResponse)
def update_ai_clarification(
    *,
    db: Session = Depends(deps.get_db),
    clarification_id: int,
    clarification_in: AIClarificationUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新AI澄清
    """
    clarification = db.query(AIClarification).filter(
        AIClarification.id == clarification_id
    ).first()

    if not clarification:
        raise HTTPException(status_code=404, detail="AI澄清记录不存在")

    clarification.answers = clarification_in.answers

    db.commit()
    db.refresh(clarification)

    return AIClarificationResponse(
        id=clarification.id,
        source_type=clarification.source_type,
        source_id=clarification.source_id,
        round=clarification.round,
        questions=clarification.questions,
        answers=clarification.answers,
        created_at=clarification.created_at,
        updated_at=clarification.updated_at
    )


@router.get("/ai-clarifications/{clarification_id}", response_model=AIClarificationResponse)
def get_ai_clarification(
    *,
    db: Session = Depends(deps.get_db),
    clarification_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取AI澄清详情
    """
    clarification = db.query(AIClarification).filter(
        AIClarification.id == clarification_id
    ).first()

    if not clarification:
        raise HTTPException(status_code=404, detail="AI澄清记录不存在")

    return AIClarificationResponse(
        id=clarification.id,
        source_type=clarification.source_type,
        source_id=clarification.source_id,
        round=clarification.round,
        questions=clarification.questions,
        answers=clarification.answers,
        created_at=clarification.created_at,
        updated_at=clarification.updated_at
    )
