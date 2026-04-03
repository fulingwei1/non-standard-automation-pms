# -*- coding: utf-8 -*-
"""
售前数据分析仪表盘 API
端点: GET /api/v1/presale/analytics/dashboard
"""
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.date_range import get_month_range
from app.core import security
from app.models.presale import (
    PresaleSolution,
    PresaleSupportTicket,
    PresaleTenderRecord,
)
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/analytics", tags=["presale-analytics-dashboard"])


@router.get("/dashboard", response_model=ResponseModel)
def get_analytics_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    售前数据分析仪表盘

    返回：
    - 核心指标卡片（工单总数/处理中/已超时/中标金额）
    - 工单趋势图（近 30 天按状态统计）
    - 中标率趋势（近 6 个月）
    - 团队工作量排行
    - 资源投入分布（按产品/行业）
    - 实时预警（超时/即将超时）
    """
    now = datetime.now()
    today = date.today()

    # ── 1. 核心指标卡片 ──
    all_tickets = db.query(PresaleSupportTicket).all()
    active_statuses = {"PENDING", "ACCEPTED", "PROCESSING", "REVIEW"}
    processing_count = sum(1 for t in all_tickets if t.status in active_statuses)

    overdue_count = sum(
        1
        for t in all_tickets
        if t.status in active_statuses and t.deadline and t.deadline < now
    )

    won_tenders = (
        db.query(PresaleTenderRecord)
        .filter(PresaleTenderRecord.result == "WON")
        .all()
    )
    won_amount = sum(float(t.our_bid_amount or 0) for t in won_tenders)

    core_metrics = {
        "total_tickets": len(all_tickets),
        "processing": processing_count,
        "overdue": overdue_count,
        "won_amount": round(won_amount, 2),
    }

    # ── 2. 工单趋势图（近 30 天按状态统计） ──
    thirty_days_ago = now - timedelta(days=30)
    recent_tickets = [
        t for t in all_tickets if t.apply_time and t.apply_time >= thirty_days_ago
    ]

    daily_trend = defaultdict(lambda: defaultdict(int))
    for t in recent_tickets:
        day_key = t.apply_time.strftime("%Y-%m-%d")
        daily_trend[day_key][t.status] += 1

    ticket_trend = []
    cursor = today - timedelta(days=29)
    while cursor <= today:
        day_str = cursor.strftime("%Y-%m-%d")
        day_data = daily_trend.get(day_str, {})
        ticket_trend.append({
            "date": day_str,
            "PENDING": day_data.get("PENDING", 0),
            "PROCESSING": day_data.get("PROCESSING", 0) + day_data.get("ACCEPTED", 0),
            "COMPLETED": day_data.get("COMPLETED", 0) + day_data.get("CLOSED", 0),
            "CANCELLED": day_data.get("CANCELLED", 0),
        })
        cursor += timedelta(days=1)

    # ── 3. 中标率趋势（近 6 个月） ──
    six_months_ago = today.replace(day=1)
    for _ in range(5):
        if six_months_ago.month == 1:
            six_months_ago = six_months_ago.replace(year=six_months_ago.year - 1, month=12)
        else:
            six_months_ago = six_months_ago.replace(month=six_months_ago.month - 1)

    tenders_period = (
        db.query(PresaleTenderRecord)
        .filter(
            PresaleTenderRecord.created_at >= datetime.combine(six_months_ago, datetime.min.time())
        )
        .all()
    )

    monthly_tenders = defaultdict(lambda: {"won": 0, "decided": 0, "won_amount": 0.0})
    for t in tenders_period:
        m = t.created_at.strftime("%Y-%m")
        if t.result in ("WON", "LOST"):
            monthly_tenders[m]["decided"] += 1
            if t.result == "WON":
                monthly_tenders[m]["won"] += 1
                monthly_tenders[m]["won_amount"] += float(t.our_bid_amount or 0)

    win_rate_trend = []
    cursor_m = six_months_ago
    while cursor_m <= today:
        m_str = cursor_m.strftime("%Y-%m")
        stats = monthly_tenders.get(m_str, {"won": 0, "decided": 0, "won_amount": 0.0})
        win_rate = (stats["won"] / stats["decided"] * 100) if stats["decided"] > 0 else 0.0
        win_rate_trend.append({
            "month": m_str,
            "win_rate": round(win_rate, 2),
            "won": stats["won"],
            "decided": stats["decided"],
            "won_amount": round(stats["won_amount"], 2),
        })
        if cursor_m.month == 12:
            cursor_m = cursor_m.replace(year=cursor_m.year + 1, month=1)
        else:
            cursor_m = cursor_m.replace(month=cursor_m.month + 1)

    # ── 4. 团队工作量排行 ──
    by_assignee = defaultdict(lambda: {
        "total": 0, "processing": 0, "completed": 0, "hours": 0.0,
    })
    for t in all_tickets:
        name = t.assignee_name or ("未分配" if not t.assignee_id else f"user_{t.assignee_id}")
        by_assignee[name]["total"] += 1
        if t.status in active_statuses:
            by_assignee[name]["processing"] += 1
        elif t.status in ("COMPLETED", "CLOSED"):
            by_assignee[name]["completed"] += 1
        by_assignee[name]["hours"] += float(t.actual_hours or 0)

    team_workload = sorted(
        [
            {
                "assignee": name,
                "total": s["total"],
                "processing": s["processing"],
                "completed": s["completed"],
                "hours": round(s["hours"], 2),
            }
            for name, s in by_assignee.items()
        ],
        key=lambda x: -x["total"],
    )

    # ── 5. 资源投入分布（按行业 / 按工单类型） ──
    by_industry = defaultdict(lambda: {"ticket_count": 0, "hours": 0.0})
    by_ticket_type = defaultdict(lambda: {"ticket_count": 0, "hours": 0.0})

    # 从方案获取行业信息关联到工单
    solutions = db.query(PresaleSolution).all()
    ticket_industry_map = {}
    for sol in solutions:
        if sol.ticket_id and sol.industry:
            ticket_industry_map[sol.ticket_id] = sol.industry

    for t in all_tickets:
        industry = ticket_industry_map.get(t.id, "未知行业")
        by_industry[industry]["ticket_count"] += 1
        by_industry[industry]["hours"] += float(t.actual_hours or 0)

        ttype = t.ticket_type or "未知"
        by_ticket_type[ttype]["ticket_count"] += 1
        by_ticket_type[ttype]["hours"] += float(t.actual_hours or 0)

    resource_distribution = {
        "by_industry": [
            {
                "industry": ind,
                "ticket_count": s["ticket_count"],
                "hours": round(s["hours"], 2),
            }
            for ind, s in sorted(by_industry.items(), key=lambda x: -x[1]["ticket_count"])
        ],
        "by_ticket_type": [
            {
                "ticket_type": tt,
                "ticket_count": s["ticket_count"],
                "hours": round(s["hours"], 2),
            }
            for tt, s in sorted(by_ticket_type.items(), key=lambda x: -x[1]["ticket_count"])
        ],
    }

    # ── 6. 实时预警（超时 / 即将超时） ──
    soon = now + timedelta(hours=24)
    alerts = []
    for t in all_tickets:
        if t.status not in active_statuses or not t.deadline:
            continue
        if t.deadline < now:
            overdue_hours = (now - t.deadline).total_seconds() / 3600
            alerts.append({
                "type": "overdue",
                "level": "danger",
                "ticket_id": t.id,
                "ticket_no": t.ticket_no,
                "title": t.title,
                "assignee_name": t.assignee_name,
                "deadline": t.deadline.isoformat(),
                "overdue_hours": round(overdue_hours, 1),
                "message": f"工单 {t.ticket_no} 已超时 {round(overdue_hours, 1)} 小时",
            })
        elif t.deadline <= soon:
            remaining_hours = (t.deadline - now).total_seconds() / 3600
            alerts.append({
                "type": "expiring_soon",
                "level": "warning",
                "ticket_id": t.id,
                "ticket_no": t.ticket_no,
                "title": t.title,
                "assignee_name": t.assignee_name,
                "deadline": t.deadline.isoformat(),
                "remaining_hours": round(remaining_hours, 1),
                "message": f"工单 {t.ticket_no} 将在 {round(remaining_hours, 1)} 小时后超时",
            })

    # 超时优先，然后按紧急程度排
    alerts.sort(key=lambda x: (0 if x["type"] == "overdue" else 1, -x.get("overdue_hours", 0)))

    return ResponseModel(
        code=200,
        message="success",
        data={
            "core_metrics": core_metrics,
            "ticket_trend": ticket_trend,
            "win_rate_trend": win_rate_trend,
            "team_workload": team_workload,
            "resource_distribution": resource_distribution,
            "alerts": alerts,
        },
    )
