# -*- coding: utf-8 -*-
"""
SLA管理 API endpoints
包含：SLA策略管理、SLA监控、SLA统计
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.service import ServiceTicket
from app.models.sla import SLAMonitor, SLAPolicy, SLAStatusEnum
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.sla import (
    SLAMonitorResponse,
    SLAPolicyCreate,
    SLAPolicyResponse,
    SLAPolicyUpdate,
    SLAStatisticsResponse,
)

router = APIRouter()


# ==================== SLA策略管理 ====================


@router.get(
    "/policies", response_model=PaginatedResponse, status_code=status.HTTP_200_OK
)
def get_sla_policies(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="每页数量",
    ),
    problem_type: Optional[str] = Query(None, description="问题类型筛选"),
    urgency: Optional[str] = Query(None, description="紧急程度筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（策略名称、编码）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取SLA策略列表
    """
    query = db.query(SLAPolicy)

    if problem_type:
        query = query.filter(
            or_(
                SLAPolicy.problem_type == problem_type, SLAPolicy.problem_type.is_(None)
            )
        )
    if urgency:
        query = query.filter(
            or_(SLAPolicy.urgency == urgency, SLAPolicy.urgency.is_(None))
        )
    if is_active is not None:
        query = query.filter(SLAPolicy.is_active == is_active)
    if keyword:
        query = query.filter(
            or_(
                SLAPolicy.policy_name.like(f"%{keyword}%"),
                SLAPolicy.policy_code.like(f"%{keyword}%"),
            )
        )

    total = query.count()
    offset = (page - 1) * page_size
    policies = (
        query.order_by(SLAPolicy.priority, desc(SLAPolicy.created_at))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    policy_list = []
    for policy in policies:
        policy_list.append(SLAPolicyResponse.model_validate(policy).model_dump())

    return PaginatedResponse(
        items=policy_list,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/policies/{policy_id}",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_sla_policy(
    *,
    db: Session = Depends(deps.get_db),
    policy_id: int = Path(..., description="策略ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取SLA策略详情
    """
    policy = db.query(SLAPolicy).filter(SLAPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="SLA策略不存在"
        )

    return ResponseModel(
        code=200,
        message="获取成功",
        data=SLAPolicyResponse.model_validate(policy).model_dump(),
    )


@router.post(
    "/policies", response_model=ResponseModel, status_code=status.HTTP_201_CREATED
)
def create_sla_policy(
    *,
    db: Session = Depends(deps.get_db),
    policy_data: SLAPolicyCreate = Body(...),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建SLA策略
    """
    # 检查策略编码是否已存在
    existing = (
        db.query(SLAPolicy)
        .filter(SLAPolicy.policy_code == policy_data.policy_code)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="策略编码已存在"
        )

    policy = SLAPolicy(
        policy_name=policy_data.policy_name,
        policy_code=policy_data.policy_code,
        problem_type=policy_data.problem_type,
        urgency=policy_data.urgency,
        response_time_hours=policy_data.response_time_hours,
        resolve_time_hours=policy_data.resolve_time_hours,
        warning_threshold_percent=policy_data.warning_threshold_percent
        or Decimal("80"),
        priority=policy_data.priority or 100,
        description=policy_data.description,
        remark=policy_data.remark,
        is_active=True,
        created_by=current_user.id,
        created_by_name=current_user.real_name or current_user.username,
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)

    return ResponseModel(
        code=200,
        message="SLA策略创建成功",
        data=SLAPolicyResponse.model_validate(policy).model_dump(),
    )


@router.put(
    "/policies/{policy_id}",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def update_sla_policy(
    *,
    db: Session = Depends(deps.get_db),
    policy_id: int = Path(..., description="策略ID"),
    policy_data: SLAPolicyUpdate = Body(...),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新SLA策略
    """
    policy = db.query(SLAPolicy).filter(SLAPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="SLA策略不存在"
        )

    update_data = policy_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(policy, key, value)

    db.commit()
    db.refresh(policy)

    return ResponseModel(
        code=200,
        message="SLA策略更新成功",
        data=SLAPolicyResponse.model_validate(policy).model_dump(),
    )


@router.delete(
    "/policies/{policy_id}",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def delete_sla_policy(
    *,
    db: Session = Depends(deps.get_db),
    policy_id: int = Path(..., description="策略ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除SLA策略（软删除：设置为不启用）
    """
    policy = db.query(SLAPolicy).filter(SLAPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="SLA策略不存在"
        )

    # 检查是否有监控记录在使用此策略
    monitor_count = (
        db.query(SLAMonitor).filter(SLAMonitor.policy_id == policy_id).count()
    )
    if monitor_count > 0:
        # 如果有监控记录，只设置为不启用
        policy.is_active = False
        db.commit()
        return ResponseModel(
            code=200, message="SLA策略已禁用（存在监控记录）", data=None
        )
    else:
        # 如果没有监控记录，可以删除
        db.delete(policy)
        db.commit()
        return ResponseModel(code=200, message="SLA策略删除成功", data=None)


# ==================== SLA监控 ====================


@router.get(
    "/monitors", response_model=PaginatedResponse, status_code=status.HTTP_200_OK
)
def get_sla_monitors(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="每页数量",
    ),
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
    offset = (page - 1) * page_size
    monitors = (
        query.order_by(desc(SLAMonitor.created_at))
        .offset(offset)
        .limit(page_size)
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
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
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


# ==================== SLA统计 ====================


@router.get("/statistics", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_sla_statistics(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    policy_id: Optional[int] = Query(None, description="策略ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取SLA统计信息
    """
    query = db.query(SLAMonitor)

    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(SLAMonitor.created_at >= start_dt)
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(SLAMonitor.created_at < end_dt)
    if policy_id:
        query = query.filter(SLAMonitor.policy_id == policy_id)

    monitors = query.all()

    total_tickets = len(monitors)
    monitored_tickets = total_tickets

    # 响应统计
    response_on_time = len([m for m in monitors if m.response_status == "ON_TIME"])
    response_overdue = len([m for m in monitors if m.response_status == "OVERDUE"])
    response_warning = len([m for m in monitors if m.response_status == "WARNING"])

    # 解决统计
    resolve_on_time = len([m for m in monitors if m.resolve_status == "ON_TIME"])
    resolve_overdue = len([m for m in monitors if m.resolve_status == "OVERDUE"])
    resolve_warning = len([m for m in monitors if m.resolve_status == "WARNING"])

    # 计算按时率
    response_rate = Decimal("0")
    if monitored_tickets > 0:
        response_rate = (
            Decimal(response_on_time) / Decimal(monitored_tickets) * Decimal("100")
        )

    resolve_rate = Decimal("0")
    if monitored_tickets > 0:
        resolve_rate = (
            Decimal(resolve_on_time) / Decimal(monitored_tickets) * Decimal("100")
        )

    # 计算平均时间
    response_times = [
        m.response_time_diff_hours
        for m in monitors
        if m.response_time_diff_hours is not None
    ]
    avg_response_time_hours = None
    if response_times:
        avg_response_time_hours = sum(response_times) / len(response_times)

    resolve_times = [
        m.resolve_time_diff_hours
        for m in monitors
        if m.resolve_time_diff_hours is not None
    ]
    avg_resolve_time_hours = None
    if resolve_times:
        avg_resolve_time_hours = sum(resolve_times) / len(resolve_times)

    # 按策略统计
    by_policy = []
    policy_stats = {}
    for monitor in monitors:
        policy_id_key = monitor.policy_id
        if policy_id_key not in policy_stats:
            policy_stats[policy_id_key] = {
                "policy_id": policy_id_key,
                "policy_name": monitor.policy.policy_name if monitor.policy else None,
                "total": 0,
                "response_on_time": 0,
                "response_overdue": 0,
                "resolve_on_time": 0,
                "resolve_overdue": 0,
            }
        stats = policy_stats[policy_id_key]
        stats["total"] += 1
        if monitor.response_status == "ON_TIME":
            stats["response_on_time"] += 1
        elif monitor.response_status == "OVERDUE":
            stats["response_overdue"] += 1
        if monitor.resolve_status == "ON_TIME":
            stats["resolve_on_time"] += 1
        elif monitor.resolve_status == "OVERDUE":
            stats["resolve_overdue"] += 1

    for stats in policy_stats.values():
        stats["response_rate"] = (
            Decimal(stats["response_on_time"])
            / Decimal(stats["total"])
            * Decimal("100")
            if stats["total"] > 0
            else Decimal("0")
        )
        stats["resolve_rate"] = (
            Decimal(stats["resolve_on_time"]) / Decimal(stats["total"]) * Decimal("100")
            if stats["total"] > 0
            else Decimal("0")
        )
        by_policy.append(stats)

    # 按问题类型统计（需要从工单获取）
    by_problem_type = []
    problem_type_stats = {}
    for monitor in monitors:
        if monitor.ticket:
            problem_type = monitor.ticket.problem_type
            if problem_type not in problem_type_stats:
                problem_type_stats[problem_type] = {
                    "problem_type": problem_type,
                    "total": 0,
                    "response_on_time": 0,
                    "response_overdue": 0,
                    "resolve_on_time": 0,
                    "resolve_overdue": 0,
                }
            stats = problem_type_stats[problem_type]
            stats["total"] += 1
            if monitor.response_status == "ON_TIME":
                stats["response_on_time"] += 1
            elif monitor.response_status == "OVERDUE":
                stats["response_overdue"] += 1
            if monitor.resolve_status == "ON_TIME":
                stats["resolve_on_time"] += 1
            elif monitor.resolve_status == "OVERDUE":
                stats["resolve_overdue"] += 1

    for stats in problem_type_stats.values():
        stats["response_rate"] = (
            Decimal(stats["response_on_time"])
            / Decimal(stats["total"])
            * Decimal("100")
            if stats["total"] > 0
            else Decimal("0")
        )
        stats["resolve_rate"] = (
            Decimal(stats["resolve_on_time"]) / Decimal(stats["total"]) * Decimal("100")
            if stats["total"] > 0
            else Decimal("0")
        )
        by_problem_type.append(stats)

    # 按紧急程度统计（需要从工单获取）
    by_urgency = []
    urgency_stats = {}
    for monitor in monitors:
        if monitor.ticket:
            urgency = monitor.ticket.urgency
            if urgency not in urgency_stats:
                urgency_stats[urgency] = {
                    "urgency": urgency,
                    "total": 0,
                    "response_on_time": 0,
                    "response_overdue": 0,
                    "resolve_on_time": 0,
                    "resolve_overdue": 0,
                }
            stats = urgency_stats[urgency]
            stats["total"] += 1
            if monitor.response_status == "ON_TIME":
                stats["response_on_time"] += 1
            elif monitor.response_status == "OVERDUE":
                stats["response_overdue"] += 1
            if monitor.resolve_status == "ON_TIME":
                stats["resolve_on_time"] += 1
            elif monitor.resolve_status == "OVERDUE":
                stats["resolve_overdue"] += 1

    for stats in urgency_stats.values():
        stats["response_rate"] = (
            Decimal(stats["response_on_time"])
            / Decimal(stats["total"])
            * Decimal("100")
            if stats["total"] > 0
            else Decimal("0")
        )
        stats["resolve_rate"] = (
            Decimal(stats["resolve_on_time"]) / Decimal(stats["total"]) * Decimal("100")
            if stats["total"] > 0
            else Decimal("0")
        )
        by_urgency.append(stats)

    statistics = SLAStatisticsResponse(
        total_tickets=total_tickets,
        monitored_tickets=monitored_tickets,
        response_on_time=response_on_time,
        response_overdue=response_overdue,
        response_warning=response_warning,
        resolve_on_time=resolve_on_time,
        resolve_overdue=resolve_overdue,
        resolve_warning=resolve_warning,
        response_rate=response_rate,
        resolve_rate=resolve_rate,
        avg_response_time_hours=Decimal(str(avg_response_time_hours))
        if avg_response_time_hours
        else None,
        avg_resolve_time_hours=Decimal(str(avg_resolve_time_hours))
        if avg_resolve_time_hours
        else None,
        by_policy=by_policy,
        by_problem_type=by_problem_type,
        by_urgency=by_urgency,
    )

    return ResponseModel(code=200, message="获取成功", data=statistics.model_dump())
