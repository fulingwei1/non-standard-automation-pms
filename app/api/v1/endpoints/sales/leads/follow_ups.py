# -*- coding: utf-8 -*-
"""
线索跟进记录管理
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Lead, LeadFollowUp
from app.models.user import User
from app.schemas.sales import (
    LeadFollowUpCreate,
    LeadFollowUpResponse,
)
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/leads/{lead_id}/follow-ups", response_model=List[LeadFollowUpResponse])
def get_lead_follow_ups(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取线索跟进记录列表
    """
    lead = get_or_404(db, Lead, lead_id, detail="线索不存在")

    follow_ups = db.query(LeadFollowUp).filter(
        LeadFollowUp.lead_id == lead_id
    ).order_by(desc(LeadFollowUp.created_at)).all()

    result = []
    for follow_up in follow_ups:
        result.append({
            "id": follow_up.id,
            "lead_id": follow_up.lead_id,
            "follow_up_type": follow_up.follow_up_type,
            "content": follow_up.content,
            "next_action": follow_up.next_action,
            "next_action_at": follow_up.next_action_at,
            "created_by": follow_up.created_by,
            "attachments": follow_up.attachments,
            "created_at": follow_up.created_at,
            "updated_at": follow_up.updated_at,
            "creator_name": follow_up.creator.real_name if follow_up.creator else None,
        })

    return result


@router.post("/leads/{lead_id}/follow-ups", response_model=LeadFollowUpResponse, status_code=201)
def create_lead_follow_up(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    follow_up_in: LeadFollowUpCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加线索跟进记录
    """
    lead = get_or_404(db, Lead, lead_id, detail="线索不存在")

    follow_up = LeadFollowUp(
        lead_id=lead_id,
        follow_up_type=follow_up_in.follow_up_type,
        content=follow_up_in.content,
        next_action=follow_up_in.next_action,
        next_action_at=follow_up_in.next_action_at,
        created_by=current_user.id,
        attachments=follow_up_in.attachments,
    )

    db.add(follow_up)

    # 如果设置了下次行动时间，更新线索的next_action_at
    if follow_up_in.next_action_at:
        lead.next_action_at = follow_up_in.next_action_at

    db.commit()
    db.refresh(follow_up)

    return {
        "id": follow_up.id,
        "lead_id": follow_up.lead_id,
        "follow_up_type": follow_up.follow_up_type,
        "content": follow_up.content,
        "next_action": follow_up.next_action,
        "next_action_at": follow_up.next_action_at,
        "created_by": follow_up.created_by,
        "attachments": follow_up.attachments,
        "created_at": follow_up.created_at,
        "updated_at": follow_up.updated_at,
        "creator_name": follow_up.creator.real_name if follow_up.creator else None,
    }
