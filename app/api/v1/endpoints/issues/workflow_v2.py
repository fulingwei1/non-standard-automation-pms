# -*- coding: utf-8 -*-
"""
问题管理 - 工作流操作（基于统一状态机框架）
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.state_machine.issue import IssueStateMachine
from app.core.state_machine.exceptions import (
    InvalidStateTransitionError,
    PermissionDeniedError,
    StateMachineValidationError,
)
from app.models.issue import IssueFollowUpRecord
from app.models.user import User
from app.schemas.issue import (
    IssueAssignRequest,
    IssueResolveRequest,
    IssueResponse,
    IssueVerifyRequest,
)

from .crud import _get_scoped_issue, get_issue

router = APIRouter()
logger = logging.getLogger(__name__)


def _create_follow_up_record(
    db: Session,
    issue_id: int,
    follow_up_type: str,
    content: str,
    operator: User,
    old_status: str = None,
    new_status: str = None,
):
    """创建跟进记录（辅助函数）"""
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type=follow_up_type,
        content=content,
        operator_id=operator.id,
        operator_name=operator.real_name or operator.username,
        old_status=old_status,
        new_status=new_status,
    )
    db.add(follow_up)


@router.post("/{issue_id}/assign", response_model=IssueResponse)
def assign_issue(
    issue_id: int,
    assign_req: IssueAssignRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:assign")),
) -> Any:
    """
    分配问题（使用状态机框架）

    状态转换: OPEN → IN_PROGRESS
    """
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 验证被分配人存在
    assignee = db.query(User).filter(User.id == assign_req.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="处理人不存在")

    # 初始化状态机
    state_machine = IssueStateMachine(issue, db)

    # 如果当前已经是 IN_PROGRESS，只更新分配信息，不触发状态转换
    if issue.status == "IN_PROGRESS":
        old_assignee_id = issue.assignee_id
        issue.assignee_id = assign_req.assignee_id
        issue.assignee_name = assignee.real_name or assignee.username
        issue.due_date = assign_req.due_date

        # 创建跟进记录
        _create_follow_up_record(
            db,
            issue_id,
            "REASSIGNMENT",
            assign_req.comment
            or f"问题重新分配给 {assignee.real_name or assignee.username}",
            current_user,
        )

        db.commit()
        db.refresh(issue)
        return get_issue(issue.id, db, current_user)

    # 执行状态转换 (OPEN → IN_PROGRESS)
    try:
        state_machine.transition_to(
            "IN_PROGRESS",
            current_user=current_user,
            comment=assign_req.comment
            or f"分配给 {assignee.real_name or assignee.username}",
            assignee_id=assign_req.assignee_id,
            assignee_name=assignee.real_name or assignee.username,
            due_date=assign_req.due_date,
        )

        # 创建跟进记录
        _create_follow_up_record(
            db,
            issue_id,
            "ASSIGNMENT",
            assign_req.comment
            or f"问题已分配给 {assignee.real_name or assignee.username}",
            current_user,
            old_status="OPEN",
            new_status="IN_PROGRESS",
        )

        db.commit()
        db.refresh(issue)

        return get_issue(issue.id, db, current_user)

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{issue_id}/resolve", response_model=IssueResponse)
def resolve_issue(
    issue_id: int,
    resolve_req: IssueResolveRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:resolve")),
) -> Any:
    """
    解决问题（使用状态机框架）

    状态转换: IN_PROGRESS → RESOLVED
    """
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 初始化状态机
    state_machine = IssueStateMachine(issue, db)

    # 执行状态转换
    try:
        state_machine.transition_to(
            "RESOLVED",
            current_user=current_user,
            comment=resolve_req.comment or "问题已解决",
            solution=resolve_req.solution,
            resolved_by=current_user.id,
            resolved_by_name=current_user.real_name or current_user.username,
        )

        # 创建跟进记录
        _create_follow_up_record(
            db,
            issue_id,
            "SOLUTION",
            resolve_req.comment or "问题已解决",
            current_user,
            old_status="IN_PROGRESS",
            new_status="RESOLVED",
        )

        db.commit()
        db.refresh(issue)

        return get_issue(issue.id, db, current_user)

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{issue_id}/verify", response_model=IssueResponse)
def verify_issue(
    issue_id: int,
    verify_req: IssueVerifyRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:verify")),
) -> Any:
    """
    验证问题（使用状态机框架）

    状态转换:
    - RESOLVED → CLOSED (验证通过)
    - RESOLVED → IN_PROGRESS (验证失败)
    """
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    if issue.status != "RESOLVED":
        raise HTTPException(status_code=400, detail="问题必须已解决才能验证")

    # 初始化状态机
    state_machine = IssueStateMachine(issue, db)

    # 根据验证结果选择不同的状态转换
    try:
        if verify_req.verified_result == "VERIFIED":
            # 验证通过: RESOLVED → CLOSED
            state_machine.transition_to(
                "CLOSED",
                current_user=current_user,
                comment=verify_req.comment or "验证通过",
                verified_by=current_user.id,
                verified_by_name=current_user.real_name or current_user.username,
            )
            new_status = "CLOSED"
        else:
            # 验证失败: RESOLVED → IN_PROGRESS
            state_machine.transition_to(
                "IN_PROGRESS",
                current_user=current_user,
                comment=verify_req.comment or "验证失败，需重新处理",
                verified_by=current_user.id,
                verified_by_name=current_user.real_name or current_user.username,
            )
            new_status = "IN_PROGRESS"

        # 创建跟进记录
        _create_follow_up_record(
            db,
            issue_id,
            "VERIFICATION",
            verify_req.comment or f"问题验证结果：{verify_req.verified_result}",
            current_user,
            old_status="RESOLVED",
            new_status=new_status,
        )

        db.commit()
        db.refresh(issue)

        return get_issue(issue.id, db, current_user)

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{issue_id}/close", response_model=IssueResponse)
def close_issue(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:close")),
    comment: str = None,
) -> Any:
    """
    直接关闭问题（使用状态机框架）

    状态转换: OPEN → CLOSED
    """
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 初始化状态机
    state_machine = IssueStateMachine(issue, db)

    # 执行状态转换
    try:
        state_machine.transition_to(
            "CLOSED", current_user=current_user, comment=comment or "直接关闭问题"
        )

        # 创建跟进记录
        _create_follow_up_record(
            db,
            issue_id,
            "STATUS_CHANGE",
            comment or "问题已关闭",
            current_user,
            old_status="OPEN",
            new_status="CLOSED",
        )

        db.commit()
        db.refresh(issue)

        return get_issue(issue.id, db, current_user)

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{issue_id}/reopen", response_model=IssueResponse)
def reopen_issue(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:reopen")),
    comment: str = None,
) -> Any:
    """
    重新打开问题（使用状态机框架）

    状态转换: CLOSED → OPEN
    """
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 初始化状态机
    state_machine = IssueStateMachine(issue, db)

    # 执行状态转换
    try:
        state_machine.transition_to(
            "OPEN", current_user=current_user, comment=comment or "重新打开问题"
        )

        # 创建跟进记录
        _create_follow_up_record(
            db,
            issue_id,
            "STATUS_CHANGE",
            comment or "问题已重新打开",
            current_user,
            old_status="CLOSED",
            new_status="OPEN",
        )

        db.commit()
        db.refresh(issue)

        return get_issue(issue.id, db, current_user)

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
