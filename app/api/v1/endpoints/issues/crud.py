# -*- coding: utf-8 -*-
"""
问题管理 - 基础CRUD操作
"""

import json
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models.issue import Issue
from app.models.user import User
from app.schemas.issue import (
    IssueCreate,
    IssueListResponse,
    IssueResponse,
    IssueUpdate,
)
from app.services.data_scope import DataScopeService

from .utils import create_blocking_issue_alert, close_blocking_issue_alerts, generate_issue_no
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


def _get_scoped_issue(db: Session, current_user: User, issue_id: int) -> Optional[Issue]:
    """获取带权限范围的问题"""
    query = db.query(Issue).options(
        joinedload(Issue.project),
        joinedload(Issue.machine),
        joinedload(Issue.service_ticket)
    ).filter(Issue.id == issue_id)
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)
    return query.first()


def build_issue_response(issue: Issue) -> IssueResponse:
    """构建问题响应对象"""
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
        impact_scope=issue.impact_scope,
        impact_level=issue.impact_level,
        is_blocking=issue.is_blocking,
        root_cause=issue.root_cause,
        responsible_engineer_id=issue.responsible_engineer_id,
        responsible_engineer_name=issue.responsible_engineer_name,
        estimated_inventory_loss=issue.estimated_inventory_loss,
        estimated_extra_hours=issue.estimated_extra_hours,
        attachments=json.loads(issue.attachments) if issue.attachments else [],
        tags=json.loads(issue.tags) if issue.tags else [],
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
    )


@router.get("/", response_model=IssueListResponse)
def list_issues(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
    category: Optional[str] = Query(None, description="问题分类"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    machine_id: Optional[int] = Query(None, description="机台ID"),
    task_id: Optional[int] = Query(None, description="任务ID"),
    issue_type: Optional[str] = Query(None, description="问题类型"),
    severity: Optional[str] = Query(None, description="严重程度"),
    priority: Optional[str] = Query(None, description="优先级"),
    issue_status: Optional[str] = Query(None, alias="status", description="状态"),
    assignee_id: Optional[int] = Query(None, description="处理人ID"),
    reporter_id: Optional[int] = Query(None, description="提出人ID"),
    responsible_engineer_id: Optional[int] = Query(None, description="责任工程师ID"),
    root_cause: Optional[str] = Query(None, description="问题原因"),
    is_blocking: Optional[bool] = Query(None, description="是否阻塞"),
    is_overdue: Optional[bool] = Query(None, description="是否逾期"),
    service_ticket_id: Optional[int] = Query(None, description="关联服务工单ID"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    search: Optional[str] = Query(None, description="关键词搜索（兼容search参数）"),
    pagination: PaginationParams = Depends(get_pagination_query),
) -> Any:
    """获取问题列表"""
    def _normalize_str_filter(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        if normalized.lower() == "all":
            return None
        return normalized

    # 兼容老前端：status/severity/category/priority 可能传 "all"（后端应视为不筛选）
    category = _normalize_str_filter(category)
    issue_type = _normalize_str_filter(issue_type)
    severity = _normalize_str_filter(severity)
    priority = _normalize_str_filter(priority)
    issue_status = _normalize_str_filter(issue_status)
    root_cause = _normalize_str_filter(root_cause)
    keyword = _normalize_str_filter(keyword) or _normalize_str_filter(search)

    query = db.query(Issue).options(joinedload(Issue.service_ticket))

    # 排除已删除的问题
    query = query.filter(Issue.status != 'DELETED')

    # 数据权限：默认仅返回与当前用户相关的问题（管理员/ALL范围除外）
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)

    # 筛选条件
    if category:
        query = query.filter(Issue.category == category)
    if project_id:
        query = query.filter(Issue.project_id == project_id)
    if machine_id:
        query = query.filter(Issue.machine_id == machine_id)
    if task_id:
        query = query.filter(Issue.task_id == task_id)
    if issue_type:
        query = query.filter(Issue.issue_type == issue_type)
    if severity:
        query = query.filter(Issue.severity == severity)
    if priority:
        query = query.filter(Issue.priority == priority)
    if issue_status:
        query = query.filter(Issue.status == issue_status)
    if assignee_id:
        query = query.filter(Issue.assignee_id == assignee_id)
    if reporter_id:
        query = query.filter(Issue.reporter_id == reporter_id)
    if responsible_engineer_id:
        query = query.filter(Issue.responsible_engineer_id == responsible_engineer_id)
    if root_cause:
        query = query.filter(Issue.root_cause == root_cause)
    if is_blocking is not None:
        query = query.filter(Issue.is_blocking == is_blocking)
    if is_overdue:
        query = query.filter(
            and_(
                Issue.due_date.isnot(None),
                Issue.due_date < date.today(),
                Issue.status.in_(['OPEN', 'PROCESSING'])
            )
        )
    if service_ticket_id:
        query = query.filter(Issue.service_ticket_id == service_ticket_id)
    if keyword:
        query = query.filter(
            or_(
                Issue.title.like(f'%{keyword}%'),
                Issue.description.like(f'%{keyword}%'),
                Issue.issue_no.like(f'%{keyword}%')
            )
        )

    # 总数
    total = query.count()

    # 分页
    issues = query.order_by(desc(Issue.created_at)).offset(pagination.offset).limit(pagination.limit).all()

    # 构建响应
    items = []
    for issue in issues:
        item = build_issue_response(issue)
        items.append(item)

    return IssueListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """获取问题详情"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    return build_issue_response(issue)


@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(
    issue_in: IssueCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:create")),
) -> Any:
    """创建问题"""
    from datetime import datetime
    
    # 生成问题编号
    issue_no = generate_issue_no(db)

    # 获取处理人名称
    assignee_name = None
    if issue_in.assignee_id:
        assignee = db.query(User).filter(User.id == issue_in.assignee_id).first()
        if assignee:
            assignee_name = assignee.real_name or assignee.username

    # 获取责任工程师名称
    responsible_engineer_name = None
    if issue_in.responsible_engineer_id:
        engineer = db.query(User).filter(User.id == issue_in.responsible_engineer_id).first()
        if engineer:
            responsible_engineer_name = engineer.real_name or engineer.username

    # 验证服务工单是否存在（如果指定了 service_ticket_id）
    if issue_in.service_ticket_id:
        from app.models.service import ServiceTicket
        ticket = db.query(ServiceTicket).filter(ServiceTicket.id == issue_in.service_ticket_id).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"服务工单不存在 (ID: {issue_in.service_ticket_id})"
            )

    # 创建问题
    issue = Issue(
        issue_no=issue_no,
        category=issue_in.category,
        project_id=issue_in.project_id,
        machine_id=issue_in.machine_id,
        task_id=issue_in.task_id,
        acceptance_order_id=issue_in.acceptance_order_id,
        related_issue_id=issue_in.related_issue_id,
        service_ticket_id=issue_in.service_ticket_id,
        issue_type=issue_in.issue_type,
        severity=issue_in.severity,
        priority=issue_in.priority,
        title=issue_in.title,
        description=issue_in.description,
        reporter_id=current_user.id,
        reporter_name=current_user.real_name or current_user.username,
        report_date=datetime.now(),
        assignee_id=issue_in.assignee_id,
        assignee_name=assignee_name,
        due_date=issue_in.due_date,
        status='OPEN',
        impact_scope=issue_in.impact_scope,
        impact_level=issue_in.impact_level,
        is_blocking=issue_in.is_blocking,
        root_cause=issue_in.root_cause,
        responsible_engineer_id=issue_in.responsible_engineer_id,
        responsible_engineer_name=responsible_engineer_name,
        estimated_inventory_loss=issue_in.estimated_inventory_loss,
        estimated_extra_hours=issue_in.estimated_extra_hours,
        attachments=str(issue_in.attachments) if issue_in.attachments else None,
        tags=str(issue_in.tags) if issue_in.tags else None,
    )

    db.add(issue)
    db.commit()
    db.refresh(issue)

    return get_issue(issue.id, db, current_user)


@router.put("/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: int,
    issue_in: IssueUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:update")),
) -> Any:
    """更新问题"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 验证服务工单是否存在（如果指定了 service_ticket_id）
    if issue_in.service_ticket_id is not None:
        from app.models.service import ServiceTicket
        ticket = db.query(ServiceTicket).filter(ServiceTicket.id == issue_in.service_ticket_id).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"服务工单不存在 (ID: {issue_in.service_ticket_id})"
            )

    # 记录阻塞状态变化
    old_is_blocking = issue.is_blocking

    # 更新字段
    update_data = issue_in.dict(exclude_unset=True)
    if 'attachments' in update_data:
        update_data['attachments'] = str(update_data['attachments'])
    if 'tags' in update_data:
        update_data['tags'] = str(update_data['tags'])
    if 'assignee_id' in update_data and update_data['assignee_id']:
        assignee = db.query(User).filter(User.id == update_data['assignee_id']).first()
        if assignee:
            update_data['assignee_name'] = assignee.real_name or assignee.username
    if 'responsible_engineer_id' in update_data and update_data['responsible_engineer_id']:
        responsible_engineer = db.query(User).filter(User.id == update_data['responsible_engineer_id']).first()
        if responsible_engineer:
            update_data['responsible_engineer_name'] = responsible_engineer.real_name or responsible_engineer.username
        elif update_data['responsible_engineer_id'] is None:
            update_data['responsible_engineer_name'] = None

    for field, value in update_data.items():
        setattr(issue, field, value)

    db.flush()

    # 处理阻塞状态变化
    try:
        new_is_blocking = issue.is_blocking
        if not old_is_blocking and new_is_blocking:
            create_blocking_issue_alert(db, issue)
        elif old_is_blocking and not new_is_blocking:
            close_blocking_issue_alerts(db, issue)
        elif old_is_blocking and new_is_blocking:
            create_blocking_issue_alert(db, issue)
    except Exception as e:
        import logging
        logging.error(f"处理阻塞问题预警失败: {str(e)}")

    db.commit()
    db.refresh(issue)

    return get_issue(issue.id, db, current_user)
