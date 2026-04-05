# -*- coding: utf-8 -*-
"""
售前资源投入预测 API
端点：GET /forecast/resource
"""

from collections import defaultdict
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.presale import (
    PresaleSolution,
    PresaleSupportTicket,
    PresaleTenderRecord,
)
from app.models.presale_expense import PresaleExpense
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/forecast", tags=["presale-forecast"])


def _safe_float(v) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


@router.get("/resource", response_model=ResponseModel)
def predict_resource_investment(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
    industry: Optional[str] = Query(None, description="行业筛选"),
    customer_type: Optional[str] = Query(None, description="客户类型"),
    product_type: Optional[str] = Query(None, description="产品/测试类型"),
    opportunity_id: Optional[int] = Query(None, description="商机ID（查找类似商机）"),
) -> Any:
    """
    售前资源投入预测

    根据历史数据预测新商机的售前投入：
    - 按行业/客户类型/产品类型的投入估算
    - 类似商机的历史投入参考
    - 投入产出比预测
    """

    # ====== 1. 历史数据采集 ======

    # 获取所有已完成的工单及其工时
    ticket_query = db.query(PresaleSupportTicket).filter(
        PresaleSupportTicket.status.in_(["COMPLETED", "CLOSED"])
    )
    all_tickets = ticket_query.all()

    # 获取所有方案
    solution_query = db.query(PresaleSolution)
    all_solutions = solution_query.all()

    # 获取费用数据
    expense_query = db.query(PresaleExpense)
    all_expenses = expense_query.all()

    # 获取投标记录
    tender_query = db.query(PresaleTenderRecord)
    all_tenders = tender_query.all()

    # ====== 2. 按维度聚合历史投入 ======

    # 按行业聚合
    industry_stats: dict[str, dict] = defaultdict(
        lambda: {
            "ticket_count": 0,
            "total_hours": 0.0,
            "solution_count": 0,
            "total_expense": 0.0,
            "won_count": 0,
            "lost_count": 0,
        }
    )

    for sol in all_solutions:
        ind = sol.industry or "未分类"
        industry_stats[ind]["solution_count"] += 1
        industry_stats[ind]["total_hours"] += _safe_float(sol.estimated_hours)

    for ticket in all_tickets:
        # 通过工单关联的方案找到行业
        related_sol = (
            db.query(PresaleSolution)
            .filter(PresaleSolution.ticket_id == ticket.id)
            .first()
        )
        ind = (related_sol.industry if related_sol else None) or "未分类"
        industry_stats[ind]["ticket_count"] += 1
        industry_stats[ind]["total_hours"] += _safe_float(ticket.actual_hours)

    for tender in all_tenders:
        # 通过投标记录关联工单找行业
        related_sol = None
        if tender.ticket_id:
            related_sol = (
                db.query(PresaleSolution)
                .filter(PresaleSolution.ticket_id == tender.ticket_id)
                .first()
            )
        ind = (related_sol.industry if related_sol else None) or "未分类"
        if tender.result == "WON":
            industry_stats[ind]["won_count"] += 1
        elif tender.result == "LOST":
            industry_stats[ind]["lost_count"] += 1

    for exp in all_expenses:
        # 简化：费用按 opportunity_id 关联行业
        ind = "未分类"
        if exp.opportunity_id:
            sol = (
                db.query(PresaleSolution)
                .filter(PresaleSolution.opportunity_id == exp.opportunity_id)
                .first()
            )
            if sol:
                ind = sol.industry or "未分类"
        industry_stats[ind]["total_expense"] += _safe_float(exp.amount)

    # ====== 3. 基于筛选条件生成预测 ======

    # 按产品/测试类型聚合
    product_stats: dict[str, dict] = defaultdict(
        lambda: {"solution_count": 0, "avg_hours": 0.0, "avg_cost": 0.0, "hours_list": []}
    )
    for sol in all_solutions:
        pt = sol.test_type or "通用"
        product_stats[pt]["solution_count"] += 1
        if sol.estimated_hours:
            product_stats[pt]["hours_list"].append(_safe_float(sol.estimated_hours))

    for pt, stats in product_stats.items():
        hrs = stats.pop("hours_list")
        stats["avg_hours"] = round(sum(hrs) / len(hrs), 1) if hrs else 0.0

    # 预测结果
    prediction = {}

    if industry and industry in industry_stats:
        s = industry_stats[industry]
        total = s["won_count"] + s["lost_count"]
        win_rate = (s["won_count"] / total * 100) if total > 0 else 0
        avg_hours = (
            s["total_hours"] / s["ticket_count"] if s["ticket_count"] > 0 else 0
        )
        avg_expense = (
            s["total_expense"] / s["ticket_count"] if s["ticket_count"] > 0 else 0
        )
        prediction["by_industry"] = {
            "industry": industry,
            "predicted_hours": round(avg_hours, 1),
            "predicted_expense": round(avg_expense, 2),
            "historical_win_rate": round(win_rate, 1),
            "sample_size": s["ticket_count"],
        }

    if product_type and product_type in product_stats:
        ps = product_stats[product_type]
        prediction["by_product_type"] = {
            "product_type": product_type,
            "predicted_hours": ps["avg_hours"],
            "sample_size": ps["solution_count"],
        }

    # ====== 4. 类似商机历史参考 ======

    similar_opportunities = []
    if opportunity_id:
        # 找到该商机关联的方案
        opp_solution = (
            db.query(PresaleSolution)
            .filter(PresaleSolution.opportunity_id == opportunity_id)
            .first()
        )
        if opp_solution:
            # 搜索同行业、同测试类型的历史方案
            similar_q = db.query(PresaleSolution).filter(
                PresaleSolution.id != opp_solution.id
            )
            if opp_solution.industry:
                similar_q = similar_q.filter(
                    PresaleSolution.industry == opp_solution.industry
                )
            if opp_solution.test_type:
                similar_q = similar_q.filter(
                    PresaleSolution.test_type == opp_solution.test_type
                )

            similar_solutions = similar_q.order_by(
                PresaleSolution.created_at.desc()
            ).limit(10).all()

            for ss in similar_solutions:
                # 查找关联的投标结果
                tender = None
                if ss.ticket_id:
                    tender = (
                        db.query(PresaleTenderRecord)
                        .filter(PresaleTenderRecord.ticket_id == ss.ticket_id)
                        .first()
                    )
                # 查找关联费用
                exp_total = 0.0
                if ss.opportunity_id:
                    exps = (
                        db.query(PresaleExpense)
                        .filter(PresaleExpense.opportunity_id == ss.opportunity_id)
                        .all()
                    )
                    exp_total = sum(_safe_float(e.amount) for e in exps)

                similar_opportunities.append({
                    "solution_id": ss.id,
                    "name": ss.name,
                    "industry": ss.industry,
                    "test_type": ss.test_type,
                    "estimated_hours": ss.estimated_hours,
                    "estimated_cost": float(ss.estimated_cost) if ss.estimated_cost else None,
                    "actual_expense": round(exp_total, 2),
                    "tender_result": tender.result if tender else None,
                    "created_at": str(ss.created_at) if ss.created_at else None,
                })

    # ====== 5. 投入产出比预测 ======

    # 全局 ROI：以中标金额 / 售前投入（工时+费用）
    total_won_amount = 0.0
    total_presale_cost = 0.0

    for tender in all_tenders:
        if tender.result == "WON" and tender.our_bid_amount:
            total_won_amount += _safe_float(tender.our_bid_amount)

    total_presale_cost = sum(_safe_float(e.amount) for e in all_expenses)
    # 加上工时折算成本（假设单位工时 200 元）
    hourly_cost_rate = 200
    total_hours = sum(_safe_float(t.actual_hours) for t in all_tickets)
    total_presale_cost += total_hours * hourly_cost_rate

    roi = (total_won_amount / total_presale_cost) if total_presale_cost > 0 else 0

    # ====== 6. 整合默认预测（无筛选条件时） ======

    if not prediction:
        # 给出全局平均值作为默认预测
        avg_hours_global = (
            total_hours / len(all_tickets) if all_tickets else 0
        )
        avg_expense_global = (
            sum(_safe_float(e.amount) for e in all_expenses) / len(all_expenses)
            if all_expenses
            else 0
        )
        prediction["global_average"] = {
            "predicted_hours": round(avg_hours_global, 1),
            "predicted_expense": round(avg_expense_global, 2),
            "sample_ticket_count": len(all_tickets),
            "sample_expense_count": len(all_expenses),
        }

    return ResponseModel(
        code=200,
        message="success",
        data={
            "prediction": prediction,
            "similar_opportunities": similar_opportunities,
            "roi_analysis": {
                "total_won_amount": round(total_won_amount, 2),
                "total_presale_cost": round(total_presale_cost, 2),
                "roi_ratio": round(roi, 2),
                "hourly_cost_rate_used": hourly_cost_rate,
            },
            "industry_overview": {
                k: {
                    "ticket_count": v["ticket_count"],
                    "solution_count": v["solution_count"],
                    "total_hours": round(v["total_hours"], 1),
                    "total_expense": round(v["total_expense"], 2),
                    "won_count": v["won_count"],
                    "lost_count": v["lost_count"],
                    "win_rate": round(
                        v["won_count"] / (v["won_count"] + v["lost_count"]) * 100, 1
                    )
                    if (v["won_count"] + v["lost_count"]) > 0
                    else 0,
                }
                for k, v in industry_stats.items()
            },
            "product_type_overview": {
                k: {
                    "solution_count": v["solution_count"],
                    "avg_hours": v["avg_hours"],
                }
                for k, v in product_stats.items()
            },
        },
    )
