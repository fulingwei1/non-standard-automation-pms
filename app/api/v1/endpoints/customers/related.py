# -*- coding: utf-8 -*-
"""
客户关联数据查询
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Customer, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/{customer_id}/projects", response_model=PaginatedResponse)
def get_customer_projects(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    current_user: User = Depends(security.require_permission("customer:read")),
) -> Any:
    """
    获取客户的项目列表
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    query = db.query(Project).filter(Project.customer_id == customer_id)
    total = query.count()
    offset = (page - 1) * page_size
    projects = query.order_by(desc(Project.created_at)).offset(offset).limit(page_size).all()

    return PaginatedResponse(
        items=projects,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )
