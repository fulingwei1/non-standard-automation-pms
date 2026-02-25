# -*- coding: utf-8 -*-
"""
客户关联数据查询
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.utils.db_helpers import get_or_404
from app.core import security
from app.models.project import Customer, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.common.query_filters import apply_pagination

router = APIRouter()


@router.get("/{customer_id}/projects", response_model=PaginatedResponse)
def get_customer_projects(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.require_permission("customer:read")),
) -> Any:
    """
    获取客户的项目列表
    """
    customer = get_or_404(db, Customer, customer_id, "客户不存在")

    query = db.query(Project).filter(Project.customer_id == customer_id)
    total = query.count()
    projects = apply_pagination(query.order_by(desc(Project.created_at)), pagination.offset, pagination.limit).all()

    return PaginatedResponse(
        items=projects,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )
