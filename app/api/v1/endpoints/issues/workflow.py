# -*- coding: utf-8 -*-
"""
问题工作流端点

包含：分配、解决、验证、状态变更操作
所有状态转换均通过 IssueStateMachine 执行，确保状态规则统一
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.core.state_machine.issue import IssueStateMachine
from app.core.state_machine.exceptions import (
    InvalidStateTransitionError,
    StateMachineValidationError,
    PermissionDeniedError,
)
from app.models.issue import Issue, IssueFollowUpRecord
from app.models.user import User
from app.schemas.issue import IssueResponse
from app.services.data_scope import DataScopeService

router = APIRouter()
logger = logging.getLogger(__name__)


class AssignRequest(BaseModel):
    """分配请求"""
    assignee_id: int
    remark: Optional[str] = None


class ResolveRequest(BaseModel):
    """解决请求"""
    solution: str
    root_cause: Optional[str] = None
    remark: Optional[str] = None


class VerifyRequest(BaseModel):
    """验证请求"""
    verified_result: str # PASSED, FAILED
    remark: Optional[str] = None


class StatusChangeRequest(BaseModel):
    """状态变更请求"""
    new_status: str
    remark: Optional[str] = None


def _get_scoped_issue(db: Session, current_user: User, issue_id: int) -> Optional[Issue]:
    """获取用户权限范围内的问题"""
    query = db.query(Issue).options(
        joinedload(Issue.service_ticket)
    ).filter(Issue.id == issue_id)
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)
    return query.first()


def _build_issue_response(issue: Issue) -> IssueResponse:
    """构建问题响应对象"""
    import json
    return IssueResponse(
        id=issue.id,
        issue_no=issue.issue_no,
        category=issue.category,
        project_id=issue.project_id,
        machine_id=issue.machine_id,
        task_id=issue.task_id,
        acceptance_order_id=issue.acceptance_order_id,
        related_issue_id=issue.related_issue_id,
        issue_type=issue.issue_type,
        severity=issue.severity,
        priority=issue.priority,
        title=issue.title,
        description=issue.description,
        reporter_id=issue.reporter_id,
        reporter_name=issue.reporter_name,
        report_date=issue.report_date,
        assignee_id=issue.assignee_id,
        assignee_name=issue.assignee_name,
        due_date=issue.due_date,
        status=issue.status,
        solution=issue.solution,
        resolved_at=issue.resolved_at,
        resolved_by=issue.resolved_by,
        resolved_by_name=issue.resolved_by_name,
        verified_at=issue.verified_at,
        verified_by=issue.verified_by,
        verified_by_name=issue.verified_by_name,
        verified_result=issue.verified_result,
        follow_up_count=issue.follow_up_count,
        last_follow_up_at=issue.last_follow_up_at,
        impact_scope=issue.impact_scope,
        impact_level=issue.impact_level,
        is_blocking=issue.is_blocking,
        attachments=json.loads(issue.attachments) if issue.attachments else [],
        tags=json.loads(issue.tags) if issue.tags else [],
        root_cause=getattr(issue, 'root_cause', None),
        responsible_engineer_id=getattr(issue, 'responsible_engineer_id', None),
        responsible_engineer_name=getattr(issue, 'responsible_engineer_name', None),
        estimated_inventory_loss=getattr(issue, 'estimated_inventory_loss', None),
        estimated_extra_hours=getattr(issue, 'estimated_extra_hours', None),
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        project_code=issue.project.project_code if issue.project else None,
        project_name=issue.project.project_name if issue.project else None,
        machine_code=issue.machine.machine_code if issue.machine else None,
        machine_name=issue.machine.machine_name if issue.machine else None,
        service_ticket_id=issue.service_ticket_id,
        service_ticket_no=issue.service_ticket.ticket_no if issue.service_ticket else None,
    )


@router.post("/{issue_id}/assign", response_model=IssueResponse)
def assign_issue(
    issue_id: int,
    request: AssignRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:update")),
) -> Any:
    """分配问题处理人（通过状态机执行）"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 获取指派人信息
    assignee = db.query(User).filter(User.id == request.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="指派用户不存在")

    assignee_name = assignee.real_name or assignee.username

    # 使用状态机执行分配（仅当 OPEN 状态才走状态机转换到 IN_PROGRESS）
    if issue.status == 'OPEN':
        sm = IssueStateMachine(issue, db)
        try:
            sm.transition_to(
                "IN_PROGRESS",
                current_user=current_user,
                comment=request.remark or f"问题已分配给 {assignee_name}",
                assignee_id=request.assignee_id,
                assignee_name=assignee_name,
            )
        except InvalidStateTransitionError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except PermissionDeniedError as e:
            raise HTTPException(status_code=403, detail=str(e))
    else:
        # 非 OPEN 状态下重新分配（仅更新分配人，不转换状态）
        if issue.status in ['CLOSED', 'CANCELLED', 'DELETED']:
            raise HTTPException(status_code=400, detail="该问题已关闭或取消，无法分配")

        old_assignee = issue.assignee_name
        issue.assignee_id = request.assignee_id
        issue.assignee_name = assignee_name

        # 记录跟进
        content = f"问题已分配给 {assignee_name}"
        if old_assignee:
            content = f"问题处理人从 {old_assignee} 变更为 {assignee_name}"
        if request.remark:
            content += f"。备注：{request.remark}"

        follow_up = IssueFollowUpRecord(
            issue_id=issue_id,
            follow_up_type='ASSIGN',
            content=content,
            operator_id=current_user.id,
            operator_name=current_user.real_name or current_user.username,
            old_status=issue.status,
            new_status=issue.status,
        )
        db.add(follow_up)
        issue.follow_up_count = (issue.follow_up_count or 0) + 1
        issue.last_follow_up_at = datetime.now()

    db.add(issue)
    db.commit()
    db.refresh(issue)

    return _build_issue_response(issue)


@router.post("/{issue_id}/resolve", response_model=IssueResponse)
def resolve_issue(
    issue_id: int,
    request: ResolveRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:update")),
) -> Any:
    """解决问题（通过状态机执行）"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 使用状态机执行解决
    sm = IssueStateMachine(issue, db)
    try:
        comment = f"解决方案：{request.solution}"
        if request.root_cause:
            comment += f"。根本原因：{request.root_cause}"
        if request.remark:
            comment += f"。备注：{request.remark}"

        sm.transition_to(
            "RESOLVED",
            current_user=current_user,
            comment=comment,
            solution=request.solution,
            resolved_by=current_user.id,
            resolved_by_name=current_user.real_name or current_user.username,
        )

        # 状态机不处理 root_cause，额外设置
        if request.root_cause:
            issue.root_cause = request.root_cause

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    db.add(issue)
    db.commit()
    db.refresh(issue)

    return _build_issue_response(issue)


@router.post("/{issue_id}/verify", response_model=IssueResponse)
def verify_issue(
    issue_id: int,
    request: VerifyRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:update")),
) -> Any:
    """验证问题解决方案（通过状态机执行）"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 使用状态机执行验证
    sm = IssueStateMachine(issue, db)
    try:
        if request.verified_result == 'PASSED':
            # 验证通过 -> CLOSED
            target_state = "CLOSED"
            comment = "问题验证通过，已关闭"
        else:
            # 验证失败 -> IN_PROGRESS
            target_state = "IN_PROGRESS"
            comment = "问题验证未通过，重新打开处理"

        if request.remark:
            comment += f"。备注：{request.remark}"

        sm.transition_to(
            target_state,
            current_user=current_user,
            comment=comment,
            verified_by=current_user.id,
            verified_by_name=current_user.real_name or current_user.username,
        )

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    db.add(issue)
    db.commit()
    db.refresh(issue)

    return _build_issue_response(issue)


@router.post("/{issue_id}/status", response_model=IssueResponse)
def change_issue_status(
    issue_id: int,
    request: StatusChangeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:update")),
) -> Any:
    """变更问题状态（通过状态机执行）"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    if issue.status == request.new_status:
        raise HTTPException(status_code=400, detail="新状态与当前状态相同")

    # 使用状态机执行状态变更
    sm = IssueStateMachine(issue, db)
    try:
        comment = f"问题状态从 {issue.status} 变更为 {request.new_status}"
        if request.remark:
            comment += f"。备注：{request.remark}"

        sm.transition_to(
            request.new_status,
            current_user=current_user,
            comment=comment,
        )

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    db.add(issue)
    db.commit()
    db.refresh(issue)

    return _build_issue_response(issue)

