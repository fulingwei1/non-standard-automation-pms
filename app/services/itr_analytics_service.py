# -*- coding: utf-8 -*-
"""
ITR流程效率分析服务
包含：问题解决时间分析、客户满意度趋势、流程瓶颈识别、SLA达成率分析
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.common.query_filters import apply_keyword_filter
from app.models.issue import Issue
from app.models.service import CustomerSatisfaction, ServiceTicket
from app.models.sla import SLAMonitor


def analyze_resolution_time(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    分析问题解决时间
    """
    # 工单解决时间分析
    ticket_query = db.query(ServiceTicket).filter(
        ServiceTicket.status == "CLOSED",
        ServiceTicket.resolved_time.isnot(None)
    )

    if start_date:
        ticket_query = ticket_query.filter(ServiceTicket.resolved_time >= start_date)
    if end_date:
        ticket_query = ticket_query.filter(ServiceTicket.resolved_time <= end_date)
    if project_id:
        ticket_query = ticket_query.filter(ServiceTicket.project_id == project_id)

    tickets = ticket_query.all()

    resolution_times = []
    for ticket in tickets:
        if ticket.reported_time and ticket.resolved_time:
            time_diff = (ticket.resolved_time - ticket.reported_time).total_seconds() / 3600  # 小时
            resolution_times.append({
                "ticket_id": ticket.id,
                "ticket_no": ticket.ticket_no,
                "problem_type": ticket.problem_type,
                "urgency": ticket.urgency,
                "resolution_hours": time_diff,
                "resolution_days": time_diff / 24,
            })

    if not resolution_times:
        return {
            "total_tickets": 0,
            "avg_resolution_hours": 0,
            "median_resolution_hours": 0,
            "min_resolution_hours": 0,
            "max_resolution_hours": 0,
            "by_problem_type": [],
            "by_urgency": [],
        }

    # 计算统计值
    hours_list = [t["resolution_hours"] for t in resolution_times]
    avg_hours = sum(hours_list) / len(hours_list)
    sorted_hours = sorted(hours_list)
    median_hours = sorted_hours[len(sorted_hours) // 2] if sorted_hours else 0
    min_hours = min(hours_list)
    max_hours = max(hours_list)

    # 按问题类型统计
    by_problem_type = {}
    for item in resolution_times:
        ptype = item["problem_type"]
        if ptype not in by_problem_type:
            by_problem_type[ptype] = []
        by_problem_type[ptype].append(item["resolution_hours"])

    by_problem_type_stats = []
    for ptype, hours in by_problem_type.items():
        by_problem_type_stats.append({
            "problem_type": ptype,
            "count": len(hours),
            "avg_hours": sum(hours) / len(hours),
            "min_hours": min(hours),
            "max_hours": max(hours),
        })

    # 按紧急程度统计
    by_urgency = {}
    for item in resolution_times:
        urgency = item["urgency"]
        if urgency not in by_urgency:
            by_urgency[urgency] = []
        by_urgency[urgency].append(item["resolution_hours"])

    by_urgency_stats = []
    for urgency, hours in by_urgency.items():
        by_urgency_stats.append({
            "urgency": urgency,
            "count": len(hours),
            "avg_hours": sum(hours) / len(hours),
            "min_hours": min(hours),
            "max_hours": max(hours),
        })

    return {
        "total_tickets": len(resolution_times),
        "avg_resolution_hours": avg_hours,
        "median_resolution_hours": median_hours,
        "min_resolution_hours": min_hours,
        "max_resolution_hours": max_hours,
        "by_problem_type": by_problem_type_stats,
        "by_urgency": by_urgency_stats,
        "details": resolution_times[:100],  # 限制返回详情数量
    }


def analyze_satisfaction_trend(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    分析客户满意度趋势
    """
    query = db.query(CustomerSatisfaction).filter(
        CustomerSatisfaction.status == "COMPLETED",
        CustomerSatisfaction.overall_score.isnot(None)
    )

    if start_date:
        query = query.filter(CustomerSatisfaction.survey_date >= start_date)
    if end_date:
        query = query.filter(CustomerSatisfaction.survey_date <= end_date)
    if project_id:
        query = apply_keyword_filter(
            query,
            CustomerSatisfaction,
            str(project_id),
            "project_code",
            use_ilike=False,
        )

    satisfactions = query.order_by(CustomerSatisfaction.survey_date).all()

    if not satisfactions:
        return {
            "total_surveys": 0,
            "avg_score": 0,
            "trend_by_month": [],
            "trend_by_type": [],
        }

    # 计算平均分
    scores = [s.overall_score for s in satisfactions if s.overall_score]
    avg_score = sum(scores) / len(scores) if scores else 0

    # 按月统计趋势
    trend_by_month = {}
    for sat in satisfactions:
        if sat.survey_date:
            month_key = sat.survey_date.strftime("%Y-%m")
            if month_key not in trend_by_month:
                trend_by_month[month_key] = {"count": 0, "total_score": 0}
            trend_by_month[month_key]["count"] += 1
            if sat.overall_score:
                trend_by_month[month_key]["total_score"] += float(sat.overall_score)

    trend_by_month_list = []
    for month, data in sorted(trend_by_month.items()):
        trend_by_month_list.append({
            "month": month,
            "count": data["count"],
            "avg_score": data["total_score"] / data["count"] if data["count"] > 0 else 0,
        })

    # 按调查类型统计
    trend_by_type = {}
    for sat in satisfactions:
        stype = sat.survey_type
        if stype not in trend_by_type:
            trend_by_type[stype] = {"count": 0, "total_score": 0}
        trend_by_type[stype]["count"] += 1
        if sat.overall_score:
            trend_by_type[stype]["total_score"] += float(sat.overall_score)

    trend_by_type_list = []
    for stype, data in trend_by_type.items():
        trend_by_type_list.append({
            "survey_type": stype,
            "count": data["count"],
            "avg_score": data["total_score"] / data["count"] if data["count"] > 0 else 0,
        })

    return {
        "total_surveys": len(satisfactions),
        "avg_score": avg_score,
        "trend_by_month": trend_by_month_list,
        "trend_by_type": trend_by_type_list,
    }


def identify_bottlenecks(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    识别流程瓶颈
    """
    # 分析各阶段停留时间
    ticket_query = db.query(ServiceTicket).filter(
        ServiceTicket.status.in_(["IN_PROGRESS", "RESOLVED", "CLOSED"])
    )

    if start_date:
        ticket_query = ticket_query.filter(ServiceTicket.created_at >= start_date)
    if end_date:
        ticket_query = ticket_query.filter(ServiceTicket.created_at <= end_date)

    tickets = ticket_query.all()

    bottlenecks = []

    # 分析PENDING到IN_PROGRESS的时间（响应时间）
    pending_to_progress = []
    for ticket in tickets:
        if ticket.assigned_time and ticket.reported_time:
            time_diff = (ticket.assigned_time - ticket.reported_time).total_seconds() / 3600
            pending_to_progress.append({
                "ticket_id": ticket.id,
                "hours": time_diff,
                "problem_type": ticket.problem_type,
            })

    if pending_to_progress:
        avg_pending_time = sum(t["hours"] for t in pending_to_progress) / len(pending_to_progress)
        bottlenecks.append({
            "stage": "PENDING → IN_PROGRESS",
            "description": "工单分配响应时间",
            "avg_hours": avg_pending_time,
            "avg_days": avg_pending_time / 24,
            "count": len(pending_to_progress),
            "severity": "HIGH" if avg_pending_time > 24 else "MEDIUM" if avg_pending_time > 8 else "LOW",
        })

    # 分析IN_PROGRESS到RESOLVED的时间（解决时间）
    progress_to_resolved = []
    for ticket in tickets:
        if ticket.resolved_time and ticket.assigned_time:
            time_diff = (ticket.resolved_time - ticket.assigned_time).total_seconds() / 3600
            progress_to_resolved.append({
                "ticket_id": ticket.id,
                "hours": time_diff,
                "problem_type": ticket.problem_type,
            })

    if progress_to_resolved:
        avg_resolve_time = sum(t["hours"] for t in progress_to_resolved) / len(progress_to_resolved)
        bottlenecks.append({
            "stage": "IN_PROGRESS → RESOLVED",
            "description": "问题解决时间",
            "avg_hours": avg_resolve_time,
            "avg_days": avg_resolve_time / 24,
            "count": len(progress_to_resolved),
            "severity": "HIGH" if avg_resolve_time > 72 else "MEDIUM" if avg_resolve_time > 24 else "LOW",
        })

    # 分析RESOLVED到CLOSED的时间（关闭时间）
    resolved_to_closed = []
    for ticket in tickets:
        if ticket.status == "CLOSED" and ticket.resolved_time:
            # 从时间线中查找关闭时间
            if ticket.timeline:
                for item in ticket.timeline:
                    if item.get("type") == "CLOSED":
                        try:
                            close_time = datetime.fromisoformat(item.get("timestamp", ""))
                            time_diff = (close_time - ticket.resolved_time).total_seconds() / 3600
                            resolved_to_closed.append({
                                "ticket_id": ticket.id,
                                "hours": time_diff,
                            })
                            break
                        except (ValueError, TypeError):
                            pass

    if resolved_to_closed:
        avg_close_time = sum(t["hours"] for t in resolved_to_closed) / len(resolved_to_closed)
        bottlenecks.append({
            "stage": "RESOLVED → CLOSED",
            "description": "工单关闭时间",
            "avg_hours": avg_close_time,
            "avg_days": avg_close_time / 24,
            "count": len(resolved_to_closed),
            "severity": "HIGH" if avg_close_time > 48 else "MEDIUM" if avg_close_time > 24 else "LOW",
        })

    # 按严重程度排序
    severity_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    bottlenecks.sort(key=lambda x: severity_order.get(x["severity"], 0), reverse=True)

    return {
        "bottlenecks": bottlenecks,
        "total_analyzed": len(tickets),
        "critical_bottlenecks": [b for b in bottlenecks if b["severity"] == "HIGH"],
    }


def analyze_sla_performance(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    policy_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    分析SLA达成率
    """
    query = db.query(SLAMonitor)

    if start_date:
        query = query.filter(SLAMonitor.created_at >= start_date)
    if end_date:
        query = query.filter(SLAMonitor.created_at <= end_date)
    if policy_id:
        query = query.filter(SLAMonitor.policy_id == policy_id)

    monitors = query.all()

    if not monitors:
        return {
            "total_monitors": 0,
            "response_rate": 0,
            "resolve_rate": 0,
            "by_policy": [],
        }

    # 响应达成率
    response_on_time = len([m for m in monitors if m.response_status == "ON_TIME"])
    response_rate = (response_on_time / len(monitors) * 100) if monitors else 0

    # 解决达成率
    resolve_on_time = len([m for m in monitors if m.resolve_status == "ON_TIME"])
    resolve_rate = (resolve_on_time / len(monitors) * 100) if monitors else 0

    # 按策略统计
    by_policy = {}
    for monitor in monitors:
        policy_id_key = monitor.policy_id
        policy_name = monitor.policy.policy_name if monitor.policy else f"Policy {policy_id_key}"

        if policy_id_key not in by_policy:
            by_policy[policy_id_key] = {
                "policy_id": policy_id_key,
                "policy_name": policy_name,
                "total": 0,
                "response_on_time": 0,
                "response_overdue": 0,
                "resolve_on_time": 0,
                "resolve_overdue": 0,
            }

        stats = by_policy[policy_id_key]
        stats["total"] += 1
        if monitor.response_status == "ON_TIME":
            stats["response_on_time"] += 1
        elif monitor.response_status == "OVERDUE":
            stats["response_overdue"] += 1
        if monitor.resolve_status == "ON_TIME":
            stats["resolve_on_time"] += 1
        elif monitor.resolve_status == "OVERDUE":
            stats["resolve_overdue"] += 1

    by_policy_list = []
    for stats in by_policy.values():
        stats["response_rate"] = (stats["response_on_time"] / stats["total"] * 100) if stats["total"] > 0 else 0
        stats["resolve_rate"] = (stats["resolve_on_time"] / stats["total"] * 100) if stats["total"] > 0 else 0
        by_policy_list.append(stats)

    return {
        "total_monitors": len(monitors),
        "response_rate": response_rate,
        "resolve_rate": resolve_rate,
        "response_on_time": response_on_time,
        "response_overdue": len([m for m in monitors if m.response_status == "OVERDUE"]),
        "resolve_on_time": resolve_on_time,
        "resolve_overdue": len([m for m in monitors if m.resolve_status == "OVERDUE"]),
        "by_policy": by_policy_list,
    }
