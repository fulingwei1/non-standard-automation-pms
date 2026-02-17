# -*- coding: utf-8 -*-
"""
售前统计 - 自动生成
从 presale.py 拆分
"""

# -*- coding: utf-8 -*-
"""
售前技术支持 API endpoints
包含：支持工单管理、技术方案管理、方案模板库、投标管理、售前统计
"""
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.query_filters import apply_like_filter
from app.core import security
from app.common.date_range import get_month_range
from app.models.presale import (
    PresaleSolution,
    PresaleSupportTicket,
    PresaleTenderRecord,
    PresaleWorkload,
)
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


def generate_ticket_no(db: Session) -> str:
    """生成工单编号：TICKET-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_ticket_query = db.query(PresaleSupportTicket)
    max_ticket_query = apply_like_filter(
        max_ticket_query,
        PresaleSupportTicket,
        f"TICKET-{today}-%",
        "ticket_no",
        use_ilike=False,
    )
    max_ticket = max_ticket_query.order_by(desc(PresaleSupportTicket.ticket_no)).first()
    if max_ticket:
        seq = int(max_ticket.ticket_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"TICKET-{today}-{seq:03d}"


def generate_solution_no(db: Session) -> str:
    """生成方案编号：SOL-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_solution_query = db.query(PresaleSolution)
    max_solution_query = apply_like_filter(
        max_solution_query,
        PresaleSolution,
        f"SOL-{today}-%",
        "solution_no",
        use_ilike=False,
    )
    max_solution = max_solution_query.order_by(desc(PresaleSolution.solution_no)).first()
    if max_solution:
        seq = int(max_solution.solution_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"SOL-{today}-{seq:03d}"


def generate_tender_no(db: Session) -> str:
    """生成投标编号：TENDER-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_tender_query = db.query(PresaleTenderRecord)
    max_tender_query = apply_like_filter(
        max_tender_query,
        PresaleTenderRecord,
        f"TENDER-{today}-%",
        "tender_no",
        use_ilike=False,
    )
    max_tender = max_tender_query.order_by(desc(PresaleTenderRecord.tender_no)).first()
    if max_tender:
        seq = int(max_tender.tender_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"TENDER-{today}-{seq:03d}"



from fastapi import APIRouter

router = APIRouter(
    prefix="/statistics",
    tags=["statistics"]
)

# 共 4 个路由

# ==================== 售前统计 ====================

@router.get("/stats/workload", response_model=ResponseModel)
def get_workload_stats(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    user_id: Optional[int] = Query(None, description="人员ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    工作量统计
    """

    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        _, end_date = get_month_range(today)

    query = db.query(PresaleWorkload).filter(
        PresaleWorkload.stat_date >= start_date,
        PresaleWorkload.stat_date <= end_date
    )

    if user_id:
        query = query.filter(PresaleWorkload.user_id == user_id)

    workloads = query.all()

    # 汇总统计
    total_pending = sum(w.pending_tickets or 0 for w in workloads)
    total_processing = sum(w.processing_tickets or 0 for w in workloads)
    total_completed = sum(w.completed_tickets or 0 for w in workloads)
    total_planned_hours = sum(float(w.planned_hours or 0) for w in workloads)
    total_actual_hours = sum(float(w.actual_hours or 0) for w in workloads)
    total_solutions = sum(w.solutions_count or 0 for w in workloads)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "summary": {
                "pending_tickets": total_pending,
                "processing_tickets": total_processing,
                "completed_tickets": total_completed,
                "total_tickets": total_pending + total_processing + total_completed,
                "planned_hours": round(total_planned_hours, 2),
                "actual_hours": round(total_actual_hours, 2),
                "solutions_count": total_solutions
            },
            "by_user": [
                {
                    "user_id": w.user_id,
                    "pending_tickets": w.pending_tickets or 0,
                    "processing_tickets": w.processing_tickets or 0,
                    "completed_tickets": w.completed_tickets or 0,
                    "planned_hours": float(w.planned_hours or 0),
                    "actual_hours": float(w.actual_hours or 0),
                    "solutions_count": w.solutions_count or 0
                }
                for w in workloads
            ]
        }
    )


@router.get("/stats/response-time", response_model=ResponseModel)
def get_response_time_stats(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    响应时效统计
    """

    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        _, end_date = get_month_range(today)

    # 统计接单响应时间（从申请到接单的时间差）
    tickets = db.query(PresaleSupportTicket).filter(
        PresaleSupportTicket.apply_time >= datetime.combine(start_date, datetime.min.time()),
        PresaleSupportTicket.apply_time <= datetime.combine(end_date, datetime.max.time()),
        PresaleSupportTicket.accept_time.isnot(None)
    ).all()

    response_times = []
    for ticket in tickets:
        if ticket.accept_time and ticket.apply_time:
            delta = ticket.accept_time - ticket.apply_time
            response_times.append(delta.total_seconds() / 3600)  # 转换为小时

    avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0

    # 统计完成时间（从接单到完成的时间差）
    completed_tickets = [t for t in tickets if t.complete_time]
    completion_times = []
    for ticket in completed_tickets:
        if ticket.complete_time and ticket.accept_time:
            delta = ticket.complete_time - ticket.accept_time
            completion_times.append(delta.total_seconds() / 3600)

    avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0.0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "response_time": {
                "total_tickets": len(tickets),
                "avg_response_hours": round(avg_response_time, 2),
                "min_response_hours": round(min(response_times), 2) if response_times else 0.0,
                "max_response_hours": round(max(response_times), 2) if response_times else 0.0
            },
            "completion_time": {
                "total_completed": len(completed_tickets),
                "avg_completion_hours": round(avg_completion_time, 2),
                "min_completion_hours": round(min(completion_times), 2) if completion_times else 0.0,
                "max_completion_hours": round(max(completion_times), 2) if completion_times else 0.0
            }
        }
    )


@router.get("/stats/conversion", response_model=ResponseModel)
def get_conversion_stats(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案转化率
    """

    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        _, end_date = get_month_range(today)

    # 统计方案数量
    total_solutions = db.query(PresaleSolution).filter(
        PresaleSolution.created_at >= datetime.combine(start_date, datetime.min.time()),
        PresaleSolution.created_at <= datetime.combine(end_date, datetime.max.time())
    ).count()

    # 统计关联商机的方案
    solutions_with_opp = db.query(PresaleSolution).filter(
        PresaleSolution.created_at >= datetime.combine(start_date, datetime.min.time()),
        PresaleSolution.created_at <= datetime.combine(end_date, datetime.max.time()),
        PresaleSolution.opportunity_id.isnot(None)
    ).count()

    # 统计转化为项目的方案（通过商机 -> 合同 -> 项目）
    from app.models.sales import Contract
    solutions_with_opp_list = db.query(PresaleSolution).filter(
        PresaleSolution.created_at >= datetime.combine(start_date, datetime.min.time()),
        PresaleSolution.created_at <= datetime.combine(end_date, datetime.max.time()),
        PresaleSolution.opportunity_id.isnot(None)
    ).all()

    converted_count = 0
    for solution in solutions_with_opp_list:
        if solution.opportunity_id:
            # 查找该商机是否有合同，且合同关联了项目
            contract = db.query(Contract).filter(
                Contract.opportunity_id == solution.opportunity_id,
                Contract.project_id.isnot(None)
            ).first()
            if contract:
                converted_count += 1

    conversion_rate = (converted_count / total_solutions * 100) if total_solutions > 0 else 0.0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "total_solutions": total_solutions,
            "solutions_with_opportunity": solutions_with_opp,
            "converted_to_projects": converted_count,
            "conversion_rate": round(conversion_rate, 2)
        }
    )


@router.get("/stats/performance", response_model=ResponseModel)
def get_performance_stats(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    user_id: Optional[int] = Query(None, description="人员ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    人员绩效
    """

    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        _, end_date = get_month_range(today)

    # 获取人员列表
    query_users = db.query(User).filter(User.is_active)
    if user_id:
        query_users = query_users.filter(User.id == user_id)
    users = query_users.all()

    performance_list = []
    for user in users:
        # 统计工单
        tickets = db.query(PresaleSupportTicket).filter(
            PresaleSupportTicket.assignee_id == user.id,
            PresaleSupportTicket.apply_time >= datetime.combine(start_date, datetime.min.time()),
            PresaleSupportTicket.apply_time <= datetime.combine(end_date, datetime.max.time())
        ).all()

        completed_tickets = [t for t in tickets if t.status == 'COMPLETED']
        total_hours = sum(float(t.actual_hours or 0) for t in completed_tickets)

        # 统计方案
        solutions = db.query(PresaleSolution).filter(
            PresaleSolution.author_id == user.id,
            PresaleSolution.created_at >= datetime.combine(start_date, datetime.min.time()),
            PresaleSolution.created_at <= datetime.combine(end_date, datetime.max.time())
        ).count()

        # 统计满意度
        rated_tickets = [t for t in completed_tickets if t.satisfaction_score]
        avg_satisfaction = sum(t.satisfaction_score for t in rated_tickets) / len(rated_tickets) if rated_tickets else 0.0

        performance_list.append({
            "user_id": user.id,
            "user_name": user.real_name or user.username,
            "total_tickets": len(tickets),
            "completed_tickets": len(completed_tickets),
            "completion_rate": (len(completed_tickets) / len(tickets) * 100) if tickets else 0.0,
            "total_hours": round(total_hours, 2),
            "solutions_count": solutions,
            "avg_satisfaction": round(avg_satisfaction, 2)
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "performance": performance_list
        }
    )
