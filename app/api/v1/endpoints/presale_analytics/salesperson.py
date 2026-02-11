# -*- coding: utf-8 -*-
"""
销售人员绩效分析端点
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.query_filters import apply_keyword_filter
from app.core import security
from app.models.enums import LeadOutcomeEnum
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.presales import SalespersonPerformance, SalespersonRanking

router = APIRouter()


@router.get(
    "/salesperson/{salesperson_id}/performance",
    response_model=ResponseModel[SalespersonPerformance],
)
async def get_salesperson_performance(
    salesperson_id: int,
    period: Optional[str] = Query(
        None, description="统计周期，格式 YYYY 或 YYYY-MM，默认全部"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(
        security.require_permission("presale_analytics:create")
    ),
) -> Any:
    """获取销售人员绩效分析"""

    salesperson = db.query(User).filter(User.id == salesperson_id).first()
    if not salesperson:
        raise HTTPException(status_code=404, detail="销售人员不存在")

    query = db.query(Project).filter(Project.salesperson_id == salesperson_id)

    if period:
        if len(period) == 7:  # YYYY-MM
            year, month = int(period[:4]), int(period[5:7])
            start_date = date(year, month, 1)
            end_date = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
        else:  # YYYY
            year = int(period)
            start_date = date(year, 1, 1)
            end_date = date(year + 1, 1, 1)
        query = query.filter(
            Project.created_at >= start_date, Project.created_at < end_date
        )

    projects = query.all()

    total_leads = len(projects)
    won_leads = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.WON.value)
    lost_leads = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.LOST.value)
    win_rate = (
        won_leads / (won_leads + lost_leads) if (won_leads + lost_leads) > 0 else 0
    )

    total_estimated_amount = sum(p.contract_amount or Decimal("0") for p in projects)
    won_amount = sum(
        p.contract_amount or Decimal("0")
        for p in projects
        if p.outcome == LeadOutcomeEnum.WON.value
    )

    from app.models.work_log import WorkLog

    total_resource_hours = 0
    wasted_hours = 0
    loss_reason_count = {}

    for project in projects:
        hours = (
            db.query(func.sum(WorkLog.work_hours))
            .filter(WorkLog.project_id == project.id)
            .scalar()
            or 0
        )
        total_resource_hours += hours

        if project.outcome in [
            LeadOutcomeEnum.LOST.value,
            LeadOutcomeEnum.ABANDONED.value,
        ]:
            wasted_hours += hours
            reason = project.loss_reason or "OTHER"
            loss_reason_count[reason] = loss_reason_count.get(reason, 0) + 1

    resource_efficiency = (
        float(won_amount) / total_resource_hours if total_resource_hours > 0 else 0
    )

    top_loss_reasons = sorted(
        loss_reason_count.items(), key=lambda x: x[1], reverse=True
    )[:3]
    top_loss_reasons = [{"reason": r, "count": c} for r, c in top_loss_reasons]

    monthly_trend = []
    today = date.today()
    for i in range(5, -1, -1):
        month_date = date(today.year, today.month, 1) - timedelta(days=30 * i)
        month_key = month_date.strftime("%Y-%m")

        month_projects = [
            p
            for p in projects
            if p.created_at and p.created_at.strftime("%Y-%m") == month_key
        ]
        month_won = sum(
            1 for p in month_projects if p.outcome == LeadOutcomeEnum.WON.value
        )
        month_lost = sum(
            1 for p in month_projects if p.outcome == LeadOutcomeEnum.LOST.value
        )
        month_rate = (
            month_won / (month_won + month_lost) if (month_won + month_lost) > 0 else 0
        )

        monthly_trend.append(
            {
                "month": month_key,
                "total": len(month_projects),
                "won": month_won,
                "lost": month_lost,
                "win_rate": round(month_rate, 3),
            }
        )

    salesperson_name = salesperson.real_name or salesperson.username

    return ResponseModel(
        code=200,
        message="查询成功",
        data=SalespersonPerformance(
            salesperson_id=salesperson_id,
            salesperson_name=salesperson_name,
            department=salesperson.department,
            total_leads=total_leads,
            won_leads=won_leads,
            lost_leads=lost_leads,
            win_rate=round(win_rate, 3),
            total_estimated_amount=total_estimated_amount,
            won_amount=won_amount,
            total_resource_hours=total_resource_hours,
            wasted_hours=wasted_hours,
            resource_efficiency=round(resource_efficiency, 2),
            top_loss_reasons=top_loss_reasons,
            monthly_trend=monthly_trend,
        ),
    )


@router.get("/salesperson-ranking", response_model=ResponseModel[SalespersonRanking])
async def get_salesperson_ranking(
    ranking_type: str = Query(
        "win_rate", description="排行类型: win_rate/efficiency/amount"
    ),
    period: str = Query(..., description="统计周期，格式 YYYY 或 YYYY-MM"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(
        security.require_permission("presale_analytics:create")
    ),
) -> Any:
    """获取销售人员排行榜"""
    from app.models.user import Role, UserRole

    # 获取所有属于销售类角色的用户
    salesp_query = db.query(User).join(UserRole).join(Role)
    salesp_query = apply_keyword_filter(salesp_query, Role, "sales", "role_code")
    salespeople = salesp_query.all()

    performances = []
    for sp in salespeople:
        query = db.query(Project).filter(Project.salesperson_id == sp.id)

        if len(period) == 7:
            year, month = int(period[:4]), int(period[5:7])
            start_date = date(year, month, 1)
            end_date = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
        else:
            year = int(period)
            start_date = date(year, 1, 1)
            end_date = date(year + 1, 1, 1)

        query = query.filter(
            Project.created_at >= start_date, Project.created_at < end_date
        )
        projects = query.all()

        if not projects:
            continue

        total = len(projects)
        won = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.WON.value)
        lost = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.LOST.value)
        win_rate = won / (won + lost) if (won + lost) > 0 else 0
        won_amount = sum(
            p.contract_amount or Decimal("0")
            for p in projects
            if p.outcome == LeadOutcomeEnum.WON.value
        )

        performances.append(
            SalespersonPerformance(
                salesperson_id=sp.id,
                salesperson_name=sp.name or sp.username,
                total_leads=total,
                won_leads=won,
                lost_leads=lost,
                win_rate=round(win_rate, 3),
                won_amount=won_amount,
                total_estimated_amount=Decimal("0"),
                total_resource_hours=0,
                wasted_hours=0,
                resource_efficiency=0,
            )
        )

    if ranking_type == "win_rate":
        performances.sort(key=lambda x: x.win_rate, reverse=True)
    elif ranking_type == "efficiency":
        performances.sort(key=lambda x: x.resource_efficiency, reverse=True)
    elif ranking_type == "amount":
        performances.sort(key=lambda x: x.won_amount, reverse=True)

    return ResponseModel(
        code=200,
        message="查询成功",
        data=SalespersonRanking(
            ranking_type=ranking_type, period=period, rankings=performances[:limit]
        ),
    )
