# -*- coding: utf-8 -*-
"""
问题操作端点

包含：关闭、取消、关联问题、项目/机台问题列表、删除
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models.issue import Issue, IssueFollowUpRecord
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.issue import (
    IssueCreate,
    IssueListResponse,
    IssueResponse,
)
from app.services.data_scope import DataScopeService

from .utils import generate_issue_no

router = APIRouter()

def _get_scoped_issue(db: Session, current_user: User, issue_id: int) -> Optional[Issue]:
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


@router.post("/{issue_id}/close", response_model=IssueResponse)
def close_issue(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """关闭问题（直接关闭，无需验证）"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    if issue.status == 'CLOSED':
        raise HTTPException(status_code=400, detail="问题已关闭")

    # 更新状态为已关闭
    old_status = issue.status
    issue.status = 'CLOSED'

    # 记录跟进记录
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type='STATUS_CHANGE',
        content='问题已关闭',
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        old_status=old_status,
        new_status='CLOSED',
    )
    db.add(follow_up)
    db.add(issue)
    db.commit()
    db.refresh(issue)

    return _build_issue_response(issue)


@router.post("/{issue_id}/cancel", response_model=IssueResponse)
def cancel_issue(
    issue_id: int,
    cancel_reason: Optional[str] = Query(None, description="取消原因"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """取消/撤销问题"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    if issue.status in ['CLOSED', 'CANCELLED']:
        raise HTTPException(status_code=400, detail="问题已关闭或已取消")

    # 更新状态为已取消
    old_status = issue.status
    issue.status = 'CANCELLED'

    # 记录跟进记录
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type='STATUS_CHANGE',
        content=f'问题已取消：{cancel_reason or "无原因"}',
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        old_status=old_status,
        new_status='CANCELLED',
    )
    db.add(follow_up)
    db.add(issue)
    db.commit()
    db.refresh(issue)

    return _build_issue_response(issue)


@router.get("/{issue_id}/related", response_model=List[IssueResponse])
def get_related_issues(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """获取关联的父子问题"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    related_issues = []

    # 获取父问题
    if issue.related_issue_id:
        parent = _get_scoped_issue(db, current_user, issue.related_issue_id)
        if parent:
            related_issues.append(_build_issue_response(parent))

    # 获取子问题
    children_query = db.query(Issue).options(
        joinedload(Issue.service_ticket)
    ).filter(Issue.related_issue_id == issue_id)
    children_query = DataScopeService.filter_issues_by_scope(db, children_query, current_user)
    children = children_query.all()
    for child in children:
        related_issues.append(_build_issue_response(child))

    return related_issues


@router.post("/{issue_id}/related", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_related_issue(
    issue_id: int,
    issue_in: IssueCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """创建关联问题（子问题或关联问题）"""
    parent_issue = _get_scoped_issue(db, current_user, issue_id)
    if not parent_issue:
        raise HTTPException(status_code=404, detail="父问题不存在")

    # 生成问题编号
    issue_no = generate_issue_no(db)

    # 创建关联问题
    issue = Issue(
        issue_no=issue_no,
        category=issue_in.category,
        project_id=issue_in.project_id or parent_issue.project_id,
        machine_id=issue_in.machine_id or parent_issue.machine_id,
        task_id=issue_in.task_id or parent_issue.task_id,
        acceptance_order_id=issue_in.acceptance_order_id or parent_issue.acceptance_order_id,
        related_issue_id=issue_id,  # 关联到父问题
        issue_type=issue_in.issue_type,
        severity=issue_in.severity,
        priority=issue_in.priority,
        title=issue_in.title,
        description=issue_in.description,
        reporter_id=current_user.id,
        reporter_name=current_user.real_name or current_user.username,
        report_date=datetime.now(),
        assignee_id=issue_in.assignee_id,
        assignee_name=db.query(User).filter(User.id == issue_in.assignee_id).first().real_name if issue_in.assignee_id else None,
        due_date=issue_in.due_date,
        status='OPEN',
        impact_scope=issue_in.impact_scope,
        impact_level=issue_in.impact_level,
        is_blocking=issue_in.is_blocking,
        attachments=str(issue_in.attachments) if issue_in.attachments else None,
        tags=str(issue_in.tags) if issue_in.tags else None,
    )

    db.add(issue)
    db.commit()
    db.refresh(issue)

    return _build_issue_response(issue)


@router.delete("/{issue_id}", response_model=ResponseModel)
def delete_issue(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:delete")),
) -> Any:
    """删除问题（软删除，仅管理员）"""
    # 检查是否为管理员
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员才能删除问题")

    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 软删除：将状态标记为DELETED
    if issue.status == 'DELETED':
        raise HTTPException(status_code=400, detail="问题已删除")

    old_status = issue.status
    issue.status = 'DELETED'

    # 创建跟进记录
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type='STATUS_CHANGE',
        content='问题已删除（管理员操作）',
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        old_status=old_status,
        new_status='DELETED',
    )
    db.add(follow_up)
    db.add(issue)
    db.commit()

    return ResponseModel(
        code=200,
        message="问题已删除"
    )
