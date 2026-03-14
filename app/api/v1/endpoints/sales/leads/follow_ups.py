# -*- coding: utf-8 -*-
"""
线索跟进记录管理
"""

from datetime import datetime, timedelta
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
    LeadFollowUpQuickCreate,
    LeadFollowUpResponse,
)
from app.utils.db_helpers import get_or_404

router = APIRouter()


QUICK_FOLLOW_UP_TEMPLATES = {
    "contacted_waiting_quote": {
        "label": "已联系，待报价",
        "follow_up_type": "CALL",
        "content": "已与客户取得联系，已确认初步需求，待发送报价单。",
        "next_action": "整理需求并发送报价单",
        "default_next_action_days": 1,
    },
    "quote_sent_waiting_feedback": {
        "label": "已报价，待反馈",
        "follow_up_type": "EMAIL",
        "content": "报价资料已发送给客户，待客户内部评审反馈。",
        "next_action": "回访客户确认报价反馈",
        "default_next_action_days": 3,
    },
    "need_technical_support": {
        "label": "需技术支援",
        "follow_up_type": "MEETING",
        "content": "客户提出技术细节问题，需安排售前工程师协同支持。",
        "next_action": "协调售前工程师并安排技术沟通",
        "default_next_action_days": 1,
    },
    "onsite_visit_planned": {
        "label": "待拜访",
        "follow_up_type": "VISIT",
        "content": "已与客户初步沟通，计划安排现场拜访进一步澄清需求。",
        "next_action": "确认拜访时间与参与人员",
        "default_next_action_days": 2,
    },
}


def _serialize_follow_up(follow_up: LeadFollowUp) -> dict:
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


def _create_follow_up_record(
    db: Session,
    *,
    lead: Lead,
    current_user: User,
    follow_up_type: str,
    content: str,
    next_action: str = None,
    next_action_at: datetime = None,
    attachments: str = None,
) -> LeadFollowUp:
    follow_up = LeadFollowUp(
        lead_id=lead.id,
        follow_up_type=follow_up_type,
        content=content,
        next_action=next_action,
        next_action_at=next_action_at,
        created_by=current_user.id,
        attachments=attachments,
    )

    db.add(follow_up)

    # 如果设置了下次行动时间，更新线索的 next_action_at
    if next_action_at:
        lead.next_action_at = next_action_at

    db.commit()
    db.refresh(follow_up)
    return follow_up


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
    get_or_404(db, Lead, lead_id, detail="线索不存在")

    follow_ups = (
        db.query(LeadFollowUp)
        .filter(LeadFollowUp.lead_id == lead_id)
        .order_by(desc(LeadFollowUp.created_at))
        .all()
    )

    return [_serialize_follow_up(follow_up) for follow_up in follow_ups]


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

    follow_up = _create_follow_up_record(
        db,
        lead=lead,
        current_user=current_user,
        follow_up_type=follow_up_in.follow_up_type,
        content=follow_up_in.content,
        next_action=follow_up_in.next_action,
        next_action_at=follow_up_in.next_action_at,
        attachments=follow_up_in.attachments,
    )

    return _serialize_follow_up(follow_up)


@router.post(
    "/leads/{lead_id}/follow-ups/quick",
    response_model=LeadFollowUpResponse,
    status_code=201,
)
def create_lead_follow_up_quick(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    quick_follow_up_in: LeadFollowUpQuickCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    快速添加线索跟进记录。

    支持：
    - 仅传模板 key，一键落一条标准跟进
    - 传 summary/content，用最少必填完成快速录入
    - 在模板基础上追加 notes / 覆盖 next_action / next_action_at
    """
    lead = get_or_404(db, Lead, lead_id, detail="线索不存在")

    template = None
    if quick_follow_up_in.template_key:
        template = QUICK_FOLLOW_UP_TEMPLATES.get(quick_follow_up_in.template_key)
        if not template:
            raise HTTPException(status_code=400, detail="不支持的快捷跟进模板")

    follow_up_type = (
        quick_follow_up_in.follow_up_type
        or (template or {}).get("follow_up_type")
        or "OTHER"
    )

    if quick_follow_up_in.content:
        content = quick_follow_up_in.content.strip()
    elif template:
        content = template["content"]
        if quick_follow_up_in.summary:
            content = f"{content} 补充：{quick_follow_up_in.summary.strip()}"
    else:
        content = quick_follow_up_in.summary.strip()

    if quick_follow_up_in.notes:
        content = f"{content}\n备注：{quick_follow_up_in.notes.strip()}"

    next_action = quick_follow_up_in.next_action
    if next_action is None and template:
        next_action = template.get("next_action")

    next_action_at = quick_follow_up_in.next_action_at
    if next_action_at is None and template and template.get("default_next_action_days") is not None:
        next_action_at = datetime.now() + timedelta(days=template["default_next_action_days"])

    follow_up = _create_follow_up_record(
        db,
        lead=lead,
        current_user=current_user,
        follow_up_type=follow_up_type,
        content=content,
        next_action=next_action,
        next_action_at=next_action_at,
        attachments=quick_follow_up_in.attachments,
    )

    return _serialize_follow_up(follow_up)
