# -*- coding: utf-8 -*-
"""
验收问题管理 - 业务操作（指派、解决、验证、延期）
"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.acceptance import AcceptanceIssue, IssueFollowUp
from app.models.user import User
from app.schemas.acceptance import (
    AcceptanceIssueAssign,
    AcceptanceIssueDefer,
    AcceptanceIssueResolve,
    AcceptanceIssueResponse,
    AcceptanceIssueVerify,
)

from .utils import build_issue_response
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.post("/acceptance-issues/{issue_id}/assign", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def assign_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    assign_in: AcceptanceIssueAssign,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    指派问题
    """
    issue = get_or_404(db, AcceptanceIssue, issue_id, "验收问题不存在")

    # 验证被指派人是否存在
    assigned_user = db.query(User).filter(User.id == assign_in.assigned_to).first()
    if not assigned_user:
        raise HTTPException(status_code=404, detail="被指派人不存在")

    # 记录原值
    old_assigned_to = issue.assigned_to

    # 更新问题
    issue.assigned_to = assign_in.assigned_to
    issue.due_date = assign_in.due_date
    issue.status = "PROCESSING" if issue.status == "OPEN" else issue.status

    db.add(issue)
    db.flush()

    # 创建跟进记录
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type="ASSIGN",
        action_content=assign_in.remark or f"问题已指派给 {assigned_user.real_name or assigned_user.username}",
        old_value=str(old_assigned_to) if old_assigned_to else None,
        new_value=str(assign_in.assigned_to),
        created_by=current_user.id
    )
    db.add(follow_up)

    db.commit()
    db.refresh(issue)

    return build_issue_response(issue, db)


@router.post("/acceptance-issues/{issue_id}/resolve", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def resolve_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    resolve_in: AcceptanceIssueResolve,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    解决问题
    """
    issue = get_or_404(db, AcceptanceIssue, issue_id, "验收问题不存在")

    if issue.status == "CLOSED":
        raise HTTPException(status_code=400, detail="问题已经关闭，无法解决")

    # 保存旧状态（用于跟进记录）
    old_status = issue.status

    # 更新问题
    issue.status = "RESOLVED"
    issue.solution = resolve_in.solution
    issue.resolved_at = datetime.now()
    issue.resolved_by = current_user.id
    if resolve_in.attachments:
        # 合并附件
        if issue.attachments:
            issue.attachments = list(issue.attachments) + resolve_in.attachments
        else:
            issue.attachments = resolve_in.attachments

    db.add(issue)
    db.flush()

    # 创建跟进记录
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type="RESOLVE",
        action_content=f"问题已解决：{resolve_in.solution}",
        old_value=old_status,
        new_value="RESOLVED",
        attachments=resolve_in.attachments,
        created_by=current_user.id
    )
    db.add(follow_up)

    db.commit()
    db.refresh(issue)

    return build_issue_response(issue, db)


@router.post("/acceptance-issues/{issue_id}/verify", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def verify_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    verify_in: AcceptanceIssueVerify,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    验证问题

    验证结果：
    - VERIFIED: 验证通过，问题已解决
    - REJECTED: 验证不通过，问题需要重新处理
    """
    issue = get_or_404(db, AcceptanceIssue, issue_id, "验收问题不存在")

    if issue.status != "RESOLVED":
        raise HTTPException(status_code=400, detail="只能验证已解决的问题")

    if verify_in.verified_result not in ["VERIFIED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="验证结果必须是 VERIFIED 或 REJECTED")

    # 记录原值
    old_status = issue.status
    old_verified_result = issue.verified_result

    # 更新问题
    issue.verified_at = datetime.now()
    issue.verified_by = current_user.id
    issue.verified_result = verify_in.verified_result

    if verify_in.verified_result == "VERIFIED":
        # 验证通过，关闭问题
        issue.status = "CLOSED"
    else:
        # 验证不通过，重新打开问题
        issue.status = "OPEN"
        issue.resolved_at = None
        issue.resolved_by = None

    db.add(issue)
    db.flush()

    # 创建跟进记录
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type="VERIFY",
        action_content=f"验证结果：{verify_in.verified_result}。{verify_in.remark or ''}",
        old_value=old_verified_result or old_status,
        new_value=verify_in.verified_result,
        created_by=current_user.id
    )
    db.add(follow_up)

    db.commit()
    db.refresh(issue)

    return build_issue_response(issue, db)


@router.post("/acceptance-issues/{issue_id}/defer", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def defer_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    defer_in: AcceptanceIssueDefer,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    延期问题
    """
    issue = get_or_404(db, AcceptanceIssue, issue_id, "验收问题不存在")

    if issue.status == "CLOSED":
        raise HTTPException(status_code=400, detail="已关闭的问题不能延期")

    # 记录原值
    old_due_date = issue.due_date

    # 更新问题
    issue.due_date = defer_in.new_due_date
    issue.status = "DEFERRED" if issue.status != "DEFERRED" else issue.status

    db.add(issue)
    db.flush()

    # 创建跟进记录
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type="STATUS_CHANGE",
        action_content=f"问题延期：{defer_in.reason}。新完成日期：{defer_in.new_due_date}",
        old_value=str(old_due_date) if old_due_date else None,
        new_value=str(defer_in.new_due_date),
        created_by=current_user.id
    )
    db.add(follow_up)

    db.commit()
    db.refresh(issue)

    return build_issue_response(issue, db)
