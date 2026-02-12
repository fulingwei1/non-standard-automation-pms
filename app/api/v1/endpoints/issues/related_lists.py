# -*- coding: utf-8 -*-
"""
关联问题列表端点

包含：项目问题列表、机台问题列表、任务问题列表、验收单问题列表
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models.acceptance import AcceptanceOrder
from app.models.issue import Issue
from app.models.progress import Task
from app.models.user import User
from app.schemas.issue import IssueListResponse, IssueResponse
from app.services.data_scope import DataScopeService
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination

router = APIRouter()


def _build_issue_list_response(
    issues: list,
    total: int,
    page: int,
    page_size: int
) -> IssueListResponse:
    """构建问题列表响应"""
    items = []
    for issue in issues:
        items.append(IssueResponse(
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
            impact_scope=issue.impact_scope,
            impact_level=issue.impact_level,
            is_blocking=issue.is_blocking,
            attachments=issue.attachments or [],
            tags=issue.tags or [],
            follow_up_count=issue.follow_up_count,
            last_follow_up_at=issue.last_follow_up_at,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            project_code=issue.project.project_code if issue.project else None,
            project_name=issue.project.project_name if issue.project else None,
            machine_code=issue.machine.machine_code if issue.machine else None,
            machine_name=issue.machine.machine_name if issue.machine else None,
            service_ticket_id=issue.service_ticket_id,
            service_ticket_no=issue.service_ticket.ticket_no if issue.service_ticket else None,
        ))

    return IssueListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.get("/projects/{project_id}/issues", response_model=IssueListResponse)
def get_project_issues(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
    pagination: PaginationParams = Depends(get_pagination_query),
    status: Optional[str] = Query(None, description="状态筛选"),
) -> Any:
    """获取项目下的所有问题"""
    query = db.query(Issue).options(
        joinedload(Issue.service_ticket)
    ).filter(
        Issue.project_id == project_id,
        Issue.status != 'DELETED'
    )
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)

    if status:
        query = query.filter(Issue.status == status)

    total = query.count()
    issues = apply_pagination(query.order_by(desc(Issue.created_at)), pagination.offset, pagination.limit).all()

    return _build_issue_list_response(issues, total, page, page_size)


@router.get("/machines/{machine_id}/issues", response_model=IssueListResponse)
def get_machine_issues(
    machine_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
    pagination: PaginationParams = Depends(get_pagination_query),
    status: Optional[str] = Query(None, description="状态筛选"),
) -> Any:
    """获取机台下的所有问题"""
    query = db.query(Issue).options(
        joinedload(Issue.service_ticket)
    ).filter(
        Issue.machine_id == machine_id,
        Issue.status != 'DELETED'
    )
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)

    if status:
        query = query.filter(Issue.status == status)

    total = query.count()
    issues = apply_pagination(query.order_by(desc(Issue.created_at)), pagination.offset, pagination.limit).all()

    return _build_issue_list_response(issues, total, page, page_size)


@router.get("/tasks/{task_id}/issues", response_model=IssueListResponse)
def get_task_issues(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
    pagination: PaginationParams = Depends(get_pagination_query),
    status: Optional[str] = Query(None, description="状态筛选"),
) -> Any:
    """获取任务下的所有问题"""
    # 验证任务是否存在
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    query = db.query(Issue).options(
        joinedload(Issue.service_ticket)
    ).filter(
        Issue.task_id == task_id,
        Issue.status != 'DELETED'
    )
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)

    if status:
        query = query.filter(Issue.status == status)

    total = query.count()
    issues = apply_pagination(query.order_by(desc(Issue.created_at)), pagination.offset, pagination.limit).all()

    return _build_issue_list_response(issues, total, page, page_size)


@router.get("/acceptance-orders/{order_id}/issues", response_model=IssueListResponse)
def get_acceptance_order_issues(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
    pagination: PaginationParams = Depends(get_pagination_query),
    status: Optional[str] = Query(None, description="状态筛选"),
) -> Any:
    """获取验收单下的所有问题"""
    # 验证验收单是否存在
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    query = db.query(Issue).filter(
        Issue.acceptance_order_id == order_id,
        Issue.status != 'DELETED'
    )
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)

    if status:
        query = query.filter(Issue.status == status)

    total = query.count()
    issues = apply_pagination(query.order_by(desc(Issue.created_at)), pagination.offset, pagination.limit).all()

    return _build_issue_list_response(issues, total, page, page_size)
