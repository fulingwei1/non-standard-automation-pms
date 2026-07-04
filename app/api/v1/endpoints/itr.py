# -*- coding: utf-8 -*-
"""ITR process endpoints backed by the real ITR services."""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services.itr_service import (
    get_issue_related_data,
    get_itr_dashboard_data,
    get_ticket_timeline,
)

router = APIRouter()


@router.get(
    "/tickets/{ticket_id}/timeline",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
def read_ticket_timeline(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """获取服务工单端到端时间线。"""
    timeline = get_ticket_timeline(db, ticket_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail="服务工单不存在或无法生成ITR时间线")
    return timeline


@router.get(
    "/issues/{issue_id}/related",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
def read_issue_related_data(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """获取问题关联的工单、验收和子问题数据。"""
    related = get_issue_related_data(db, issue_id)
    if related is None:
        raise HTTPException(status_code=404, detail="问题不存在或无法生成ITR关联数据")
    return related


@router.get("/dashboard", response_model=dict, status_code=status.HTTP_200_OK)
def read_itr_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """获取 ITR 流程看板数据。"""
    dashboard = get_itr_dashboard_data(
        db,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
    )
    if dashboard is None:
        raise HTTPException(status_code=500, detail="无法生成ITR看板数据")
    return dashboard


__all__ = ["router"]
