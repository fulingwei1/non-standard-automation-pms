# -*- coding: utf-8 -*-
"""
评审参与人管理端点
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.technical_review import ReviewParticipant, TechnicalReview
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.technical_review import (
    ReviewParticipantCreate,
    ReviewParticipantResponse,
    ReviewParticipantUpdate,
)
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

router = APIRouter()


@router.post("/technical-reviews/{review_id}/participants", response_model=ReviewParticipantResponse, status_code=status.HTTP_201_CREATED)
def create_review_participant(
    review_id: int,
    participant_in: ReviewParticipantCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """添加评审参与人"""
    review = get_or_404(db, TechnicalReview, review_id, "技术评审不存在")

    existing = db.query(ReviewParticipant).filter(
        ReviewParticipant.review_id == review_id,
        ReviewParticipant.user_id == participant_in.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该用户已参与评审")

    participant = ReviewParticipant(
        review_id=review_id,
        user_id=participant_in.user_id,
        role=participant_in.role,
        is_required=participant_in.is_required,
    )

    db.add(participant)
    db.commit()
    db.refresh(participant)

    return ReviewParticipantResponse(
        id=participant.id,
        review_id=participant.review_id,
        user_id=participant.user_id,
        role=participant.role,
        is_required=participant.is_required,
        attendance=participant.attendance,
        delegate_id=participant.delegate_id,
        sign_time=participant.sign_time,
        signature=participant.signature,
        created_at=participant.created_at,
    )


@router.put("/technical-reviews/participants/{participant_id}", response_model=ReviewParticipantResponse, status_code=status.HTTP_200_OK)
def update_review_participant(
    participant_id: int,
    participant_in: ReviewParticipantUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新评审参与人（签到、委派等）"""
    participant = get_or_404(db, ReviewParticipant, participant_id, "评审参与人不存在")

    update_data = participant_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(participant, field, value)

    if participant_in.attendance == 'CONFIRMED' and not participant.sign_time:
        participant.sign_time = datetime.now()

    db.commit()
    db.refresh(participant)

    return ReviewParticipantResponse(
        id=participant.id,
        review_id=participant.review_id,
        user_id=participant.user_id,
        role=participant.role,
        is_required=participant.is_required,
        attendance=participant.attendance,
        delegate_id=participant.delegate_id,
        sign_time=participant.sign_time,
        signature=participant.signature,
        created_at=participant.created_at,
    )


@router.delete("/technical-reviews/participants/{participant_id}", status_code=status.HTTP_200_OK)
def delete_review_participant(
    participant_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """删除评审参与人"""
    participant = get_or_404(db, ReviewParticipant, participant_id, "评审参与人不存在")

    db.delete(participant)
    db.commit()

    return ResponseModel(message="评审参与人已删除")
