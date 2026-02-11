# -*- coding: utf-8 -*-
"""
服务工单管理 - 问题关联
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.issue import Issue
from app.models.service import ServiceTicket
from app.models.user import User
from app.schemas.issue import IssueListResponse

router = APIRouter()


@router.get("/{ticket_id}/issues", response_model=IssueListResponse, status_code=status.HTTP_200_OK)
def get_ticket_related_issues(
    ticket_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
    pagination: PaginationParams = Depends(get_pagination_query),
) -> Any:
    """获取工单关联的问题列表"""
    # 验证工单是否存在
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    # 查询关联的问题
    from app.api.v1.endpoints.issues.crud import build_issue_response

    query = db.query(Issue).options(
        joinedload(Issue.service_ticket)
    ).filter(
        Issue.service_ticket_id == ticket_id,
        Issue.status != 'DELETED'
    )

    total = query.count()
    issues = apply_pagination(query.order_by(desc(Issue.created_at)), pagination.offset, pagination.limit).all()

    items = [build_issue_response(issue) for issue in issues]

    return IssueListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )
