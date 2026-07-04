# -*- coding: utf-8 -*-
"""
服务工单管理 - 问题关联
"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.ecn import Ecn
from app.models.issue import Issue
from app.models.service import ServiceTicket
from app.models.user import User
from app.schemas.ecn import EcnResponse
from app.schemas.issue import IssueResponse
from app.schemas.issue import IssueListResponse
from app.services.data_scope import DataScopeService

from ..access import ensure_service_ticket_access_or_raise

router = APIRouter()


class TicketIssueEscalation(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    issue_type: str = "SERVICE_QUALITY"
    severity: str = "MAJOR"
    priority: str | None = None
    root_cause: str | None = None
    assignee_id: int | None = None
    is_blocking: bool = False


class TicketEcnEscalation(BaseModel):
    ecn_title: str | None = Field(default=None, max_length=200)
    ecn_type: str = "QUALITY_ISSUE"
    change_reason: str | None = None
    change_description: str | None = None
    change_scope: str = "PARTIAL"
    priority: str | None = None
    urgency: str | None = None


def _ticket_priority(ticket: ServiceTicket) -> str:
    urgency = str(ticket.urgency or "MEDIUM").upper()
    if urgency in {"URGENT", "CRITICAL"}:
        return "URGENT"
    if urgency == "HIGH":
        return "HIGH"
    if urgency == "LOW":
        return "LOW"
    return "MEDIUM"


def _append_ticket_timeline(ticket: ServiceTicket, entry: dict) -> None:
    timeline = list(ticket.timeline or [])
    timeline.append(entry)
    ticket.timeline = timeline


@router.get("/{ticket_id}/issues", response_model=IssueListResponse, status_code=status.HTTP_200_OK)
def get_ticket_related_issues(
    ticket_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
    pagination: PaginationParams = Depends(get_pagination_query),
) -> Any:
    """获取工单关联的问题列表"""
    # 验证工单是否存在
    ensure_service_ticket_access_or_raise(db, current_user, ticket_id, "您没有权限访问该工单关联的问题")

    # 查询关联的问题
    from app.api.v1.endpoints.issues.crud import build_issue_response

    query = (
        db.query(Issue)
        .options(joinedload(Issue.service_ticket))
        .filter(Issue.service_ticket_id == ticket_id, Issue.status != "DELETED")
    )
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)

    total = query.count()
    issues = apply_pagination(
        query.order_by(desc(Issue.created_at)), pagination.offset, pagination.limit
    ).all()

    items = [build_issue_response(issue) for issue in issues]

    return IssueListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.post(
    "/{ticket_id}/issues",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
)
def escalate_ticket_to_issue(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    escalation_in: TicketIssueEscalation,
    current_user: User = Depends(security.require_permission("service:update")),
) -> Any:
    """将服务工单升级为质量问题。"""
    ticket = ensure_service_ticket_access_or_raise(
        db, current_user, ticket_id, "您没有权限升级该工单为质量问题"
    )

    if escalation_in.assignee_id:
        assignee = db.query(User).filter(User.id == escalation_in.assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="处理负责人不存在")
        assignee_name = assignee.real_name or assignee.username
    else:
        assignee_name = None

    from app.api.v1.endpoints.issues.crud import build_issue_response
    from app.api.v1.endpoints.issues.utils import generate_issue_no

    issue = Issue(
        issue_no=generate_issue_no(db),
        category="QUALITY",
        project_id=ticket.project_id,
        machine_id=ticket.machine_id,
        service_ticket_id=ticket.id,
        issue_type=escalation_in.issue_type,
        severity=escalation_in.severity,
        priority=escalation_in.priority or _ticket_priority(ticket),
        title=escalation_in.title or f"服务工单质量问题：{ticket.ticket_no}",
        description=escalation_in.description or ticket.problem_desc,
        reporter_id=current_user.id,
        reporter_name=current_user.real_name or current_user.username,
        report_date=datetime.now(),
        assignee_id=escalation_in.assignee_id,
        assignee_name=assignee_name,
        status="OPEN",
        impact_scope="SERVICE_TICKET",
        impact_level=escalation_in.severity,
        is_blocking=escalation_in.is_blocking,
        root_cause=escalation_in.root_cause,
    )
    db.add(issue)
    db.flush()

    _append_ticket_timeline(
        ticket,
        {
            "type": "ISSUE_ESCALATED",
            "timestamp": datetime.now().isoformat(),
            "user": current_user.real_name or current_user.username,
            "description": f"已升级为质量问题 {issue.issue_no}",
            "issue_id": issue.id,
        },
    )
    db.add(ticket)
    db.commit()
    db.refresh(issue)

    return build_issue_response(issue)


@router.post(
    "/{ticket_id}/ecn",
    response_model=EcnResponse,
    status_code=status.HTTP_201_CREATED,
)
def escalate_ticket_to_ecn(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    escalation_in: TicketEcnEscalation,
    current_user: User = Depends(security.require_permission("service:update")),
) -> Any:
    """将服务工单升级为 ECN 草稿。"""
    ticket = ensure_service_ticket_access_or_raise(
        db, current_user, ticket_id, "您没有权限升级该工单为ECN"
    )

    if not ticket.project_id:
        raise HTTPException(status_code=400, detail="服务工单未关联项目，不能升级为ECN")

    from app.api.v1.endpoints.ecn.utils import build_ecn_response, generate_ecn_no

    ecn = Ecn(
        ecn_no=generate_ecn_no(db),
        ecn_title=escalation_in.ecn_title or f"服务工单ECN：{ticket.ticket_no}",
        ecn_type=escalation_in.ecn_type,
        source_type="SERVICE_TICKET",
        source_no=ticket.ticket_no,
        source_id=ticket.id,
        project_id=ticket.project_id,
        machine_id=ticket.machine_id,
        change_reason=escalation_in.change_reason or ticket.problem_desc,
        change_description=escalation_in.change_description or ticket.problem_desc,
        change_scope=escalation_in.change_scope,
        priority=escalation_in.priority or _ticket_priority(ticket),
        urgency=escalation_in.urgency or ticket.urgency,
        status="DRAFT",
        current_step="DRAFT",
        applicant_id=current_user.id,
        applicant_name=current_user.real_name or current_user.username,
        applicant_dept=current_user.department,
        created_by=current_user.id,
    )
    db.add(ecn)
    db.flush()

    _append_ticket_timeline(
        ticket,
        {
            "type": "ECN_ESCALATED",
            "timestamp": datetime.now().isoformat(),
            "user": current_user.real_name or current_user.username,
            "description": f"已升级为ECN {ecn.ecn_no}",
            "ecn_id": ecn.id,
        },
    )
    db.add(ticket)
    db.commit()
    db.refresh(ecn)

    return build_ecn_response(db, ecn)
