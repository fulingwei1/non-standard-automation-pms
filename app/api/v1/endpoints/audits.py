# -*- coding: utf-8 -*-
"""
权限审计 API endpoints
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.user import PermissionAudit, User
from app.schemas.common import PaginatedResponse
from app.common.query_filters import apply_pagination
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

router = APIRouter()


class PermissionAuditResponse(BaseModel):
    """权限审计响应"""
    id: int
    operator_id: int
    operator_name: Optional[str] = None
    action: str
    target_type: str
    target_id: int
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PermissionAuditListResponse(PaginatedResponse):
    """权限审计列表响应"""
    items: List[PermissionAuditResponse]


@router.get("/", response_model=PermissionAuditListResponse, status_code=status.HTTP_200_OK)
def read_audits(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    operator_id: Optional[int] = Query(None, description="操作人ID筛选"),
    target_type: Optional[str] = Query(None, description="目标类型筛选（user/role/permission）"),
    target_id: Optional[int] = Query(None, description="目标ID筛选"),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("audit:read")),
) -> Any:
    """
    获取权限审计日志列表（支持分页和筛选）

    - **page**: 页码，从1开始
    - **page_size**: 每页数量，默认20，最大100
    - **operator_id**: 操作人ID筛选
    - **target_type**: 目标类型筛选
    - **target_id**: 目标ID筛选
    - **action**: 操作类型筛选
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    """
    query = db.query(PermissionAudit)

    # 操作人筛选
    if operator_id:
        query = query.filter(PermissionAudit.operator_id == operator_id)

    # 目标类型筛选
    if target_type:
        query = query.filter(PermissionAudit.target_type == target_type)

    # 目标ID筛选
    if target_id:
        query = query.filter(PermissionAudit.target_id == target_id)

    # 操作类型筛选
    if action:
        query = query.filter(PermissionAudit.action == action)

    # 日期范围筛选
    if start_date:
        query = query.filter(PermissionAudit.created_at >= start_date)
    if end_date:
        query = query.filter(PermissionAudit.created_at <= end_date)

    # 计算总数
    total = query.count()

    # 分页
    audits = apply_pagination(query.order_by(PermissionAudit.created_at.desc()), pagination.offset, pagination.limit).all()

    # 构建响应数据
    items = []
    for audit in audits:
        operator_name = None
        if audit.operator:
            operator_name = audit.operator.real_name or audit.operator.username

        items.append(PermissionAuditResponse(
            id=audit.id,
            operator_id=audit.operator_id,
            operator_name=operator_name,
            action=audit.action,
            target_type=audit.target_type,
            target_id=audit.target_id,
            detail=audit.detail,
            ip_address=audit.ip_address,
            user_agent=audit.user_agent,
            created_at=audit.created_at
        ))

    return PermissionAuditListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.get("/{audit_id}", response_model=PermissionAuditResponse, status_code=status.HTTP_200_OK)
def read_audit(
    audit_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("audit:read")),
) -> Any:
    """
    获取权限审计日志详情

    - **audit_id**: 审计日志ID
    """
    audit = get_or_404(db, PermissionAudit, audit_id, "审计日志不存在")

    operator_name = None
    if audit.operator:
        operator_name = audit.operator.real_name or audit.operator.username

    return PermissionAuditResponse(
        id=audit.id,
        operator_id=audit.operator_id,
        operator_name=operator_name,
        action=audit.action,
        target_type=audit.target_type,
        target_id=audit.target_id,
        detail=audit.detail,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        created_at=audit.created_at
    )



