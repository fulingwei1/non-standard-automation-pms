# -*- coding: utf-8 -*-
"""权限审计日志查询 API。"""

import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import PermissionAudit, User
from app.schemas.common import ResponseModel

router = APIRouter()


def _audit_to_dict(audit: PermissionAudit) -> dict[str, Any]:
    detail: Any = audit.detail
    if isinstance(detail, str) and detail:
        try:
            detail = json.loads(detail)
        except json.JSONDecodeError:
            detail = {"raw": detail}

    operator = getattr(audit, "operator", None)
    return {
        "id": audit.id,
        "operator_id": audit.operator_id,
        "operator_name": getattr(operator, "display_name", None) if operator else None,
        "action": audit.action,
        "target_type": audit.target_type,
        "target_id": audit.target_id,
        "detail": detail,
        "ip_address": audit.ip_address,
        "user_agent": audit.user_agent,
        "created_at": audit.created_at,
        "updated_at": audit.updated_at,
    }


@router.get("/", response_model=ResponseModel[dict[str, Any]])
def read_audits(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    operator_id: Optional[int] = Query(None, description="操作人ID筛选"),
    target_type: Optional[str] = Query(None, description="目标类型筛选（user/role/permission）"),
    target_id: Optional[int] = Query(None, description="目标ID筛选"),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:read")),
) -> ResponseModel[dict[str, Any]]:
    """获取权限审计日志列表（支持分页和筛选）。"""
    query = db.query(PermissionAudit)

    if operator_id is not None:
        query = query.filter(PermissionAudit.operator_id == operator_id)
    if target_type:
        query = query.filter(PermissionAudit.target_type == target_type)
    if target_id is not None:
        query = query.filter(PermissionAudit.target_id == target_id)
    if action:
        query = query.filter(PermissionAudit.action == action)
    if start_date is not None:
        query = query.filter(PermissionAudit.created_at >= start_date)
    if end_date is not None:
        query = query.filter(PermissionAudit.created_at <= end_date)

    total = query.count()
    items = (
        query.order_by(PermissionAudit.created_at.desc(), PermissionAudit.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ResponseModel(
        code=200,
        message="获取审计日志成功",
        data={
            "items": [_audit_to_dict(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size else 0,
        },
    )


@router.get("/{audit_id}", response_model=ResponseModel[dict[str, Any]])
def read_audit(
    audit_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:read")),
) -> ResponseModel[dict[str, Any]]:
    """获取权限审计日志详情。"""
    audit = db.query(PermissionAudit).filter(PermissionAudit.id == audit_id).first()
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审计日志不存在",
        )
    return ResponseModel(code=200, message="获取审计日志成功", data=_audit_to_dict(audit))


__all__ = ["router", "read_audits", "read_audit"]
