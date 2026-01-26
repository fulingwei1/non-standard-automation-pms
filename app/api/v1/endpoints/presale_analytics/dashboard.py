# -*- coding: utf-8 -*-
"""
售前分析仪表板端点
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import LeadOutcomeEnum
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.presales import PresalesDashboardData

router = APIRouter()


@router.get("/dashboard", response_model=ResponseModel[PresalesDashboardData])
async def get_presales_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("presale_analytics:create"))
) -> Any:
    """获取售前分析仪表板数据"""

    today = date.today()
    year_start = date(today.year, 1, 1)

    # 年度统计
    ytd_projects = db.query(Project).filter(
        Project.created_at >= year_start
    ).all()

    total_leads_ytd = len(ytd_projects)
    won_leads_ytd = sum(1 for p in ytd_projects if p.outcome == LeadOutcomeEnum.WON.value)
    lost_leads_ytd = sum(1 for p in ytd_projects if p.outcome == LeadOutcomeEnum.LOST.value)
    overall_win_rate = won_leads_ytd / (won_leads_ytd + lost_leads_ytd) if (won_leads_ytd + lost_leads_ytd) > 0 else 0

    # 资源浪费统计
    from app.models.work_log import WorkLog

    total_hours = 0
    wasted_hours = 0
    loss_reasons = {}

    for project in ytd_projects:
        hours = db.query(func.sum(WorkLog.work_hours)).filter(
            WorkLog.project_id == project.id
        ).scalar() or 0
        total_hours += hours

        if project.outcome in [LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value]:
            wasted_hours += hours
            reason = project.loss_reason or 'OTHER'
            loss_reasons[reason] = loss_reasons.get(reason, 0) + 1

    avg_investment = total_hours / total_leads_ytd if total_leads_ytd > 0 else 0
    waste_rate = wasted_hours / total_hours if total_hours > 0 else 0
    wasted_cost = Decimal(str(wasted_hours)) * Decimal('300')

    # 月度统计（近6个月）
    monthly_stats = []
    for i in range(5, -1, -1):
        month_date = date(today.year, today.month, 1) - timedelta(days=30 * i)
        month_key = month_date.strftime('%Y-%m')

        month_projects = [p for p in ytd_projects if p.created_at and p.created_at.strftime('%Y-%m') == month_key]
        month_won = sum(1 for p in month_projects if p.outcome == LeadOutcomeEnum.WON.value)
        month_lost = sum(1 for p in month_projects if p.outcome == LeadOutcomeEnum.LOST.value)

        monthly_stats.append({
            "month": month_key,
            "total": len(month_projects),
            "won": month_won,
            "lost": month_lost,
            "win_rate": round(month_won / (month_won + month_lost), 3) if (month_won + month_lost) > 0 else 0
        })

    return ResponseModel(
        code=200,
        message="查询成功",
        data=PresalesDashboardData(
            total_leads_ytd=total_leads_ytd,
            won_leads_ytd=won_leads_ytd,
            overall_win_rate=round(overall_win_rate, 3),
            avg_investment_per_lead=round(avg_investment, 1),
            total_wasted_hours=wasted_hours,
            total_wasted_cost=wasted_cost,
            waste_rate=round(waste_rate, 3),
            monthly_stats=monthly_stats,
            loss_reason_distribution=loss_reasons
        )
    )
