# -*- coding: utf-8 -*-
"""
问题管理 - 跟进记录操作
"""

from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.issue import Issue, IssueFollowUpRecord
from app.models.user import User
from app.schemas.issue import IssueFollowUpCreate, IssueFollowUpResponse

from .crud import _get_scoped_issue

router = APIRouter()


@router.get("/{issue_id}/follow-ups", response_model=List[IssueFollowUpResponse])
def get_issue_follow_ups(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """获取问题跟进记录"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    follow_ups = db.query(IssueFollowUpRecord).filter(
        IssueFollowUpRecord.issue_id == issue_id
    ).order_by(desc(IssueFollowUpRecord.created_at)).all()

    return [
        IssueFollowUpResponse(
            id=fu.id,
            issue_id=fu.issue_id,
            follow_up_type=fu.follow_up_type,
            content=fu.content,
            operator_id=fu.operator_id,
            operator_name=fu.operator_name,
            old_status=fu.old_status,
            new_status=fu.new_status,
            attachments=fu.attachments or [],
            created_at=fu.created_at,
        )
        for fu in follow_ups
    ]


@router.post("/{issue_id}/follow-ups", response_model=IssueFollowUpResponse, status_code=status.HTTP_201_CREATED)
def create_issue_follow_up(
    issue_id: int,
    follow_up_in: IssueFollowUpCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """创建问题跟进记录"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type=follow_up_in.follow_up_type,
        content=follow_up_in.content,
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        old_status=follow_up_in.old_status,
        new_status=follow_up_in.new_status,
        attachments=str(follow_up_in.attachments) if follow_up_in.attachments else None,
    )

    db.add(follow_up)

    # 更新问题的跟进统计
    issue.follow_up_count = db.query(IssueFollowUpRecord).filter(IssueFollowUpRecord.issue_id == issue_id).count()
    issue.last_follow_up_at = datetime.now()

    db.commit()
    db.refresh(follow_up)

    return IssueFollowUpResponse(
        id=follow_up.id,
        issue_id=follow_up.issue_id,
        follow_up_type=follow_up.follow_up_type,
        content=follow_up.content,
        operator_id=follow_up.operator_id,
        operator_name=follow_up.operator_name,
        old_status=follow_up.old_status,
        new_status=follow_up.new_status,
        attachments=follow_up.attachments or [],
        created_at=follow_up.created_at,
    )
