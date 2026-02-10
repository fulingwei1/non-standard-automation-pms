# -*- coding: utf-8 -*-
"""
SLA监控端点
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sla import SLAMonitor
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.sla import SLAMonitorResponse
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


@router.get(
    "/monitors", response_model=PaginatedResponse, status_code=status.HTTP_200_OK
)
def get_sla_monitors(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    ticket_id: Optional[int] = Query(None, description="工单ID筛选"),
    policy_id: Optional[int] = Query(None, description="策略ID筛选"),
    response_status: Optional[str] = Query(None, description="响应状态筛选"),
    resolve_status: Optional[str] = Query(None, description="解决状态筛选"),
    overdue_only: Optional[bool] = Query(False, description="仅显示超时记录"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取SLA监控记录列表
    """

    query = db.query(SLAMonitor)

    if ticket_id:
        query = query.filter(SLAMonitor.ticket_id == ticket_id)
    if policy_id:
        query = query.filter(SLAMonitor.policy_id == policy_id)
    if response_status:
        query = query.filter(SLAMonitor.response_status == response_status)
    if resolve_status:
        query = query.filter(SLAMonitor.resolve_status == resolve_status)
    if overdue_only:
        query = query.filter(
            or_(
                SLAMonitor.response_status == "OVERDUE",
                SLAMonitor.resolve_status == "OVERDUE",
            )
        )

    total = query.count()
    monitors = (
        query.order_by(desc(SLAMonitor.created_at))
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    monitor_list = []
    for monitor in monitors:
        monitor_dict = SLAMonitorResponse.model_validate(monitor).model_dump()
        # 添加工单号和策略信息
        if monitor.ticket:
            monitor_dict["ticket_no"] = monitor.ticket.ticket_no
        if monitor.policy:
            monitor_dict["policy_name"] = monitor.policy.policy_name
            monitor_dict["policy_code"] = monitor.policy.policy_code
        monitor_list.append(monitor_dict)

    return PaginatedResponse(
        items=monitor_list,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.get(
    "/monitors/{monitor_id}",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_sla_monitor(
    *,
    db: Session = Depends(deps.get_db),
    monitor_id: int = Path(..., description="监控记录ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取SLA监控记录详情
    """
    monitor = db.query(SLAMonitor).filter(SLAMonitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="SLA监控记录不存在"
        )

    monitor_dict = SLAMonitorResponse.model_validate(monitor).model_dump()
    if monitor.ticket:
        monitor_dict["ticket_no"] = monitor.ticket.ticket_no
    if monitor.policy:
        monitor_dict["policy_name"] = monitor.policy.policy_name
        monitor_dict["policy_code"] = monitor.policy.policy_code

    return ResponseModel(code=200, message="获取成功", data=monitor_dict)
