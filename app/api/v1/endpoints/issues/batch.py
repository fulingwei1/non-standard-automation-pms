# -*- coding: utf-8 -*-
"""
问题批量操作端点

包含：批量分配、批量状态变更、批量关闭
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.issue import Issue, IssueFollowUpRecord
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.data_scope_service import DataScopeService

router = APIRouter()

def _get_scoped_issue(db: Session, current_user: User, issue_id: int) -> Optional[Issue]:
    query = db.query(Issue).filter(Issue.id == issue_id)
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)
    return query.first()


@router.post("/batch-assign", response_model=ResponseModel)
def batch_assign_issues(
    *,
    db: Session = Depends(deps.get_db),
    issue_ids: List[int] = Body(..., description="问题ID列表"),
    assignee_id: int = Body(..., description="处理人ID"),
    due_date: Optional[date] = Body(None, description="要求完成日期"),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """批量分配问题"""
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="处理人不存在")

    success_count = 0
    failed_issues = []

    for issue_id in issue_ids:
        try:
            issue = _get_scoped_issue(db, current_user, issue_id)
            if not issue:
                failed_issues.append({"issue_id": issue_id, "reason": "问题不存在"})
                continue

            issue.assignee_id = assignee_id
            issue.assignee_name = assignee.real_name or assignee.username
            if due_date:
                issue.due_date = due_date

            # 创建跟进记录
            follow_up = IssueFollowUpRecord(
                issue_id=issue_id,
                follow_up_type='ASSIGNMENT',
                content=f"批量分配给 {assignee.real_name or assignee.username}",
                operator_id=current_user.id,
                operator_name=current_user.real_name or current_user.username,
                old_status=None,
                new_status=None,
            )
            db.add(follow_up)
            db.add(issue)
            success_count += 1
        except Exception as e:
            failed_issues.append({"issue_id": issue_id, "reason": str(e)})

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量分配完成：成功 {success_count} 个，失败 {len(failed_issues)} 个",
        data={"success_count": success_count, "failed_issues": failed_issues}
    )


@router.post("/batch-status", response_model=ResponseModel)
def batch_change_issue_status(
    *,
    db: Session = Depends(deps.get_db),
    issue_ids: List[int] = Body(..., description="问题ID列表"),
    new_status: str = Body(..., description="新状态"),
    comment: Optional[str] = Body(None, description="备注"),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """批量更新问题状态"""
    success_count = 0
    failed_issues = []

    for issue_id in issue_ids:
        try:
            issue = _get_scoped_issue(db, current_user, issue_id)
            if not issue:
                failed_issues.append({"issue_id": issue_id, "reason": "问题不存在"})
                continue

            old_status = issue.status
            issue.status = new_status

            # 创建跟进记录
            follow_up = IssueFollowUpRecord(
                issue_id=issue_id,
                follow_up_type='STATUS_CHANGE',
                content=comment or f"批量状态变更：{old_status} → {new_status}",
                operator_id=current_user.id,
                operator_name=current_user.real_name or current_user.username,
                old_status=old_status,
                new_status=new_status,
            )
            db.add(follow_up)
            db.add(issue)
            success_count += 1
        except Exception as e:
            failed_issues.append({"issue_id": issue_id, "reason": str(e)})

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量状态变更完成：成功 {success_count} 个，失败 {len(failed_issues)} 个",
        data={"success_count": success_count, "failed_issues": failed_issues}
    )


@router.post("/batch-close", response_model=ResponseModel)
def batch_close_issues(
    *,
    db: Session = Depends(deps.get_db),
    issue_ids: List[int] = Body(..., description="问题ID列表"),
    comment: Optional[str] = Body(None, description="关闭原因"),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """批量关闭问题"""
    success_count = 0
    failed_issues = []

    for issue_id in issue_ids:
        try:
            issue = _get_scoped_issue(db, current_user, issue_id)
            if not issue:
                failed_issues.append({"issue_id": issue_id, "reason": "问题不存在"})
                continue

            if issue.status == 'CLOSED':
                failed_issues.append({"issue_id": issue_id, "reason": "问题已关闭"})
                continue

            old_status = issue.status
            issue.status = 'CLOSED'

            # 创建跟进记录
            follow_up = IssueFollowUpRecord(
                issue_id=issue_id,
                follow_up_type='STATUS_CHANGE',
                content=comment or "批量关闭",
                operator_id=current_user.id,
                operator_name=current_user.real_name or current_user.username,
                old_status=old_status,
                new_status='CLOSED',
            )
            db.add(follow_up)
            db.add(issue)
            success_count += 1
        except Exception as e:
            failed_issues.append({"issue_id": issue_id, "reason": str(e)})

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量关闭完成：成功 {success_count} 个，失败 {len(failed_issues)} 个",
        data={"success_count": success_count, "failed_issues": failed_issues}
    )
