# -*- coding: utf-8 -*-
"""
SLA统计端点
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sla import SLAMonitor
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sla import SLAStatisticsResponse

router = APIRouter()


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
