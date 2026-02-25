# -*- coding: utf-8 -*-
"""
验收问题管理 - 跟进记录
"""
from typing import Any, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.acceptance import AcceptanceIssue, IssueFollowUp
from app.models.user import User
from app.schemas.acceptance import (
    IssueFollowUpCreate,
    IssueFollowUpResponse,
)
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/acceptance-issues/{issue_id}/follow-ups", response_model=List[IssueFollowUpResponse], status_code=status.HTTP_200_OK)
def read_issue_follow_ups(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取问题跟进记录
    """
    get_or_404(db, AcceptanceIssue, issue_id, "验收问题不存在")

    follow_ups = db.query(IssueFollowUp).filter(IssueFollowUp.issue_id == issue_id).order_by(IssueFollowUp.created_at).all()

    items = []
    for follow_up in follow_ups:
        created_by_name = None
        if follow_up.created_by:
            user = db.query(User).filter(User.id == follow_up.created_by).first()
            created_by_name = user.real_name or user.username if user else None

        items.append(IssueFollowUpResponse(
            id=follow_up.id,
            issue_id=follow_up.issue_id,
            action_type=follow_up.action_type,
            action_content=follow_up.action_content,
            old_value=follow_up.old_value,
            new_value=follow_up.new_value,
            attachments=follow_up.attachments,
            created_by=follow_up.created_by,
            created_by_name=created_by_name,
            created_at=follow_up.created_at
        ))

    return items


@router.post("/acceptance-issues/{issue_id}/follow-ups", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_issue_follow_up(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    follow_up_in: IssueFollowUpCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加跟进记录
    """
    get_or_404(db, AcceptanceIssue, issue_id, "验收问题不存在")

    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type=follow_up_in.action_type,
        action_content=follow_up_in.action_content,
        attachments=follow_up_in.attachments,
        created_by=current_user.id
    )

    db.add(follow_up)
    db.commit()

    return ResponseModel(message="跟进记录添加成功")
