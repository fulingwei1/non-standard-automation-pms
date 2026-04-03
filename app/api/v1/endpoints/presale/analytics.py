# -*- coding: utf-8 -*-
"""
售前高级分析 API
包含：SLA 监控、投标结果分析、资源投入产出比
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
from app.models.sales.leads import Opportunity
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/analytics", tags=["presale-analytics"])


# ==================== 1. SLA 监控 ====================


@router.get("/tickets/sla-monitor", response_model=ResponseModel)
def get_sla_monitor(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    assignee_id: Optional[int] = Query(None, description="处理人ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    售前工单 SLA 监控

    返回即将超时、已超时工单，以及 SLA 达标率统计。
    SLA 判定规则：工单 deadline 字段为截止时间，
    - 已超时：未完成且 deadline < 当前时间
    - 即将超时：未完成且 deadline 在未来 24 小时内
    - SLA 达标：在 deadline 之前完成
    """
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        _, end_date = get_month_range(today)

    now = datetime.now()
    soon = now + timedelta(hours=24)

    # 基础查询：时间范围内的工单
    base_query = db.query(PresaleSupportTicket).filter(
        PresaleSupportTicket.apply_time >= datetime.combine(start_date, datetime.min.time()),
        PresaleSupportTicket.apply_time <= datetime.combine(end_date, datetime.max.time()),
    )
    if assignee_id:
        base_query = base_query.filter(PresaleSupportTicket.assignee_id == assignee_id)

    all_tickets = base_query.all()

    # 活跃状态（未完成/未关闭/未取消）
    active_statuses = {"PENDING", "ACCEPTED", "PROCESSING", "REVIEW"}

    # 分类
    overdue_tickets = []
    expiring_soon_tickets = []
    sla_met_count = 0
    sla_missed_count = 0
    total_with_deadline = 0

    # 按人员/按类型的 SLA 统计
    by_assignee = defaultdict(lambda: {"total": 0, "met": 0, "missed": 0})
    by_type = defaultdict(lambda: {"total": 0, "met": 0, "missed": 0})

    for t in all_tickets:
        if not t.deadline:
            continue

        total_with_deadline += 1
        assignee_key = t.assignee_name or f"user_{t.assignee_id}" if t.assignee_id else "未分配"
        type_key = t.ticket_type or "未知"

        by_assignee[assignee_key]["total"] += 1
        by_type[type_key]["total"] += 1

        if t.status in active_statuses:
            # 未完成的工单检查超时
            if t.deadline < now:
                overdue_tickets.append(_ticket_brief(t))
                sla_missed_count += 1
                by_assignee[assignee_key]["missed"] += 1
                by_type[type_key]["missed"] += 1
            elif t.deadline <= soon:
                expiring_soon_tickets.append(_ticket_brief(t))
                # 即将超时但还没超，暂不计入 missed
                by_assignee[assignee_key]["met"] += 1
                by_type[type_key]["met"] += 1
            else:
                by_assignee[assignee_key]["met"] += 1
                by_type[type_key]["met"] += 1
        else:
            # 已完成/已关闭的工单，判断是否在 deadline 前完成
            finish_time = t.complete_time or t.updated_at
            if finish_time and finish_time <= t.deadline:
                sla_met_count += 1
                by_assignee[assignee_key]["met"] += 1
                by_type[type_key]["met"] += 1
            else:
                sla_missed_count += 1
                by_assignee[assignee_key]["missed"] += 1
                by_type[type_key]["missed"] += 1

    sla_rate = (sla_met_count / total_with_deadline * 100) if total_with_deadline > 0 else 0.0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "summary": {
                "total_tickets": len(all_tickets),
                "total_with_deadline": total_with_deadline,
                "sla_met": sla_met_count,
                "sla_missed": sla_missed_count,
                "sla_rate": round(sla_rate, 2),
            },
            "overdue_tickets": overdue_tickets,
            "expiring_soon_tickets": expiring_soon_tickets,
            "by_assignee": [
                {
                    "assignee": name,
                    "total": stats["total"],
                    "met": stats["met"],
                    "missed": stats["missed"],
                    "sla_rate": round(
                        (stats["met"] / stats["total"] * 100) if stats["total"] > 0 else 0.0, 2
                    ),
                }
                for name, stats in sorted(by_assignee.items())
            ],
            "by_ticket_type": [
                {
                    "ticket_type": ttype,
                    "total": stats["total"],
                    "met": stats["met"],
                    "missed": stats["missed"],
                    "sla_rate": round(
                        (stats["met"] / stats["total"] * 100) if stats["total"] > 0 else 0.0, 2
                    ),
                }
                for ttype, stats in sorted(by_type.items())
            ],
        },
    )


def _ticket_brief(t: PresaleSupportTicket) -> dict:
    """工单摘要，用于超时/即将超时列表"""
    now = datetime.now()
    remaining = (t.deadline - now).total_seconds() / 3600 if t.deadline > now else 0
    overdue_hours = (now - t.deadline).total_seconds() / 3600 if t.deadline < now else 0
    return {
        "id": t.id,
        "ticket_no": t.ticket_no,
        "title": t.title,
        "ticket_type": t.ticket_type,
        "urgency": t.urgency,
        "status": t.status,
        "customer_name": t.customer_name,
        "assignee_name": t.assignee_name,
        "deadline": t.deadline.isoformat() if t.deadline else None,
        "remaining_hours": round(remaining, 1),
        "overdue_hours": round(overdue_hours, 1),
    }


# ==================== 2. 投标结果分析 ====================


@router.get("/tenders/analysis", response_model=ResponseModel)
def get_tender_deep_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    投标结果深度分析

    返回中标率、输单原因、竞争对手分析、金额趋势。
    """
    today = date.today()
    if not start_date:
        start_date = date(today.year, 1, 1)  # 默认当年
    if not end_date:
        _, end_date = get_month_range(today)

    tenders = (
        db.query(PresaleTenderRecord)
        .filter(
            PresaleTenderRecord.created_at >= datetime.combine(start_date, datetime.min.time()),
            PresaleTenderRecord.created_at <= datetime.combine(end_date, datetime.max.time()),
        )
        .all()
    )

    total = len(tenders)
    decided = [t for t in tenders if t.result in ("WON", "LOST")]
    won = [t for t in tenders if t.result == "WON"]
    lost = [t for t in tenders if t.result == "LOST"]

    win_rate = (len(won) / len(decided) * 100) if decided else 0.0
    won_amount = sum(float(t.our_bid_amount or 0) for t in won)
    lost_amount = sum(float(t.our_bid_amount or 0) for t in lost)

    # --- 按月趋势 ---
    monthly = defaultdict(lambda: {"total": 0, "won": 0, "lost": 0, "won_amount": 0.0})
    for t in tenders:
        m = t.created_at.strftime("%Y-%m")
        monthly[m]["total"] += 1
        if t.result == "WON":
            monthly[m]["won"] += 1
            monthly[m]["won_amount"] += float(t.our_bid_amount or 0)
        elif t.result == "LOST":
            monthly[m]["lost"] += 1

    # --- 按销售（leader）统计 ---
    by_leader = defaultdict(lambda: {"total": 0, "won": 0, "lost": 0})
    leader_ids = {t.leader_id for t in tenders if t.leader_id}
    leader_map = {}
    if leader_ids:
        leaders = db.query(User).filter(User.id.in_(leader_ids)).all()
        leader_map = {u.id: u.real_name or u.username for u in leaders}

    for t in tenders:
        name = leader_map.get(t.leader_id, f"user_{t.leader_id}") if t.leader_id else "未指定"
        by_leader[name]["total"] += 1
        if t.result == "WON":
            by_leader[name]["won"] += 1
        elif t.result == "LOST":
            by_leader[name]["lost"] += 1

    # --- 输单原因分析 ---
    loss_reasons = defaultdict(int)
    for t in lost:
        reason = (t.result_reason or "未填写原因").strip()
        # 简单分类：取前20字符作为摘要 key，避免过长
        loss_reasons[reason] += 1

    # --- 竞争对手分析 ---
    competitor_stats = defaultdict(lambda: {"encounter": 0, "we_won": 0, "we_lost": 0})
    for t in decided:
        competitors = t.competitors if isinstance(t.competitors, list) else []
        for comp in competitors:
            comp_name = comp.get("name", comp) if isinstance(comp, dict) else str(comp)
            if not comp_name:
                continue
            competitor_stats[comp_name]["encounter"] += 1
            if t.result == "WON":
                competitor_stats[comp_name]["we_won"] += 1
            else:
                competitor_stats[comp_name]["we_lost"] += 1

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "summary": {
                "total_tenders": total,
                "decided": len(decided),
                "won": len(won),
                "lost": len(lost),
                "pending": total - len(decided),
                "win_rate": round(win_rate, 2),
                "won_amount": round(won_amount, 2),
                "lost_amount": round(lost_amount, 2),
            },
            "monthly_trend": [
                {
                    "month": m,
                    "total": s["total"],
                    "won": s["won"],
                    "lost": s["lost"],
                    "won_amount": round(s["won_amount"], 2),
                    "win_rate": round(
                        (s["won"] / (s["won"] + s["lost"]) * 100)
                        if (s["won"] + s["lost"]) > 0
                        else 0.0,
                        2,
                    ),
                }
                for m, s in sorted(monthly.items())
            ],
            "by_leader": [
                {
                    "leader": name,
                    "total": s["total"],
                    "won": s["won"],
                    "lost": s["lost"],
                    "win_rate": round(
                        (s["won"] / (s["won"] + s["lost"]) * 100)
                        if (s["won"] + s["lost"]) > 0
                        else 0.0,
                        2,
                    ),
                }
                for name, s in sorted(by_leader.items())
            ],
            "loss_reasons": [
                {"reason": reason, "count": count}
                for reason, count in sorted(loss_reasons.items(), key=lambda x: -x[1])
            ],
            "competitor_analysis": [
                {
                    "competitor": name,
                    "encounters": s["encounter"],
                    "we_won": s["we_won"],
                    "we_lost": s["we_lost"],
                    "win_rate_vs": round(
                        (s["we_won"] / s["encounter"] * 100) if s["encounter"] > 0 else 0.0, 2
                    ),
                }
                for name, s in sorted(
                    competitor_stats.items(), key=lambda x: -x[1]["encounter"]
                )
            ],
        },
    )


# ==================== 3. 资源投入产出比 ====================


@router.get("/roi-analysis", response_model=ResponseModel)
def get_roi_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    售前资源投入产出比分析

    将工单工时（投入）与投标中标金额（产出）关联，计算各维度 ROI。
    """
    today = date.today()
    if not start_date:
        start_date = date(today.year, 1, 1)
    if not end_date:
        _, end_date = get_month_range(today)

    dt_start = datetime.combine(start_date, datetime.min.time())
    dt_end = datetime.combine(end_date, datetime.max.time())

    # 获取时间范围内的工单（含工时信息）
    tickets = (
        db.query(PresaleSupportTicket)
        .filter(
            PresaleSupportTicket.apply_time >= dt_start,
            PresaleSupportTicket.apply_time <= dt_end,
        )
        .all()
    )

    # 获取时间范围内的投标记录
    tenders = (
        db.query(PresaleTenderRecord)
        .filter(
            PresaleTenderRecord.created_at >= dt_start,
            PresaleTenderRecord.created_at <= dt_end,
        )
        .all()
    )

    # 建立 ticket_id -> tender 映射
    tender_by_ticket = defaultdict(list)
    for t in tenders:
        if t.ticket_id:
            tender_by_ticket[t.ticket_id].append(t)

    # 建立 opportunity_id -> tender 结果映射
    won_tenders_by_opp = {}
    for t in tenders:
        if t.result == "WON" and t.opportunity_id:
            won_tenders_by_opp[t.opportunity_id] = t

    # 总体统计
    total_hours = sum(float(t.actual_hours or 0) for t in tickets)
    total_won_amount = sum(float(t.our_bid_amount or 0) for t in tenders if t.result == "WON")
    overall_roi = (total_won_amount / total_hours) if total_hours > 0 else 0.0

    # --- 按客户统计 ---
    by_customer = defaultdict(lambda: {"hours": 0.0, "won_amount": 0.0, "ticket_count": 0, "won_count": 0})
    for t in tickets:
        cname = t.customer_name or "未知客户"
        by_customer[cname]["hours"] += float(t.actual_hours or 0)
        by_customer[cname]["ticket_count"] += 1

    for t in tenders:
        if t.result == "WON":
            cname = t.customer_name or "未知客户"
            by_customer[cname]["won_amount"] += float(t.our_bid_amount or 0)
            by_customer[cname]["won_count"] += 1

    # --- 按工单类型统计 ---
    by_type = defaultdict(lambda: {"hours": 0.0, "ticket_count": 0})
    for t in tickets:
        ttype = t.ticket_type or "未知"
        by_type[ttype]["hours"] += float(t.actual_hours or 0)
        by_type[ttype]["ticket_count"] += 1

    # --- 按处理人统计 ---
    by_assignee = defaultdict(lambda: {"hours": 0.0, "ticket_count": 0, "completed": 0})
    for t in tickets:
        aname = t.assignee_name or (f"user_{t.assignee_id}" if t.assignee_id else "未分配")
        by_assignee[aname]["hours"] += float(t.actual_hours or 0)
        by_assignee[aname]["ticket_count"] += 1
        if t.status in ("COMPLETED", "CLOSED"):
            by_assignee[aname]["completed"] += 1

    # --- 高 ROI 客户特征（投入少、产出高）---
    high_roi_customers = []
    for cname, stats in by_customer.items():
        if stats["won_amount"] > 0 and stats["hours"] > 0:
            roi = stats["won_amount"] / stats["hours"]
            high_roi_customers.append({
                "customer": cname,
                "hours": round(stats["hours"], 2),
                "won_amount": round(stats["won_amount"], 2),
                "roi_per_hour": round(roi, 2),
                "ticket_count": stats["ticket_count"],
                "won_count": stats["won_count"],
            })
    high_roi_customers.sort(key=lambda x: -x["roi_per_hour"])

    # --- 资源优化建议 ---
    suggestions = _generate_roi_suggestions(
        total_hours, total_won_amount, by_customer, by_type, high_roi_customers
    )

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "summary": {
                "total_hours": round(total_hours, 2),
                "total_won_amount": round(total_won_amount, 2),
                "roi_per_hour": round(overall_roi, 2),
                "total_tickets": len(tickets),
                "total_tenders": len(tenders),
                "won_tenders": len([t for t in tenders if t.result == "WON"]),
            },
            "by_customer": [
                {
                    "customer": cname,
                    "hours": round(s["hours"], 2),
                    "won_amount": round(s["won_amount"], 2),
                    "roi_per_hour": round(
                        (s["won_amount"] / s["hours"]) if s["hours"] > 0 else 0.0, 2
                    ),
                    "ticket_count": s["ticket_count"],
                    "won_count": s["won_count"],
                }
                for cname, s in sorted(by_customer.items(), key=lambda x: -x[1]["won_amount"])
            ],
            "by_ticket_type": [
                {
                    "ticket_type": ttype,
                    "hours": round(s["hours"], 2),
                    "ticket_count": s["ticket_count"],
                    "avg_hours": round(
                        (s["hours"] / s["ticket_count"]) if s["ticket_count"] > 0 else 0.0, 2
                    ),
                }
                for ttype, s in sorted(by_type.items(), key=lambda x: -x[1]["hours"])
            ],
            "by_assignee": [
                {
                    "assignee": aname,
                    "hours": round(s["hours"], 2),
                    "ticket_count": s["ticket_count"],
                    "completed": s["completed"],
                    "avg_hours_per_ticket": round(
                        (s["hours"] / s["ticket_count"]) if s["ticket_count"] > 0 else 0.0, 2
                    ),
                }
                for aname, s in sorted(by_assignee.items(), key=lambda x: -x[1]["hours"])
            ],
            "high_roi_customers": high_roi_customers[:10],
            "suggestions": suggestions,
        },
    )


def _generate_roi_suggestions(
    total_hours: float,
    total_won_amount: float,
    by_customer: dict,
    by_type: dict,
    high_roi_customers: list,
) -> list:
    """基于数据生成资源优化建议"""
    suggestions = []

    if total_hours == 0:
        suggestions.append({"type": "info", "message": "暂无工时数据，建议完善工单工时记录以获取分析"})
        return suggestions

    overall_roi = total_won_amount / total_hours if total_hours > 0 else 0

    # 找出投入多但产出低的客户
    low_roi_customers = []
    for cname, stats in by_customer.items():
        if stats["hours"] > total_hours * 0.1 and stats["won_amount"] == 0:
            low_roi_customers.append(cname)

    if low_roi_customers:
        suggestions.append({
            "type": "warning",
            "message": f"以下客户投入较多工时但无中标产出，建议评估继续投入的必要性：{', '.join(low_roi_customers[:5])}",
        })

    # 高 ROI 客户建议
    if high_roi_customers:
        top = high_roi_customers[0]
        suggestions.append({
            "type": "positive",
            "message": f"客户「{top['customer']}」ROI 最高（{top['roi_per_hour']} 元/工时），建议优先分配资源",
        })

    # 工单类型建议
    type_hours = sorted(by_type.items(), key=lambda x: -x[1]["hours"])
    if type_hours:
        top_type = type_hours[0]
        suggestions.append({
            "type": "info",
            "message": f"「{top_type[0]}」类型工单消耗最多工时（{round(top_type[1]['hours'], 1)} 小时），"
            f"可考虑标准化模板以降低投入",
        })

    return suggestions
