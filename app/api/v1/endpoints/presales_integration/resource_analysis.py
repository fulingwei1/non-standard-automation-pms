# -*- coding: utf-8 -*-
"""
资源投入与浪费分析端点
"""

from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import LeadOutcomeEnum
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.presales import ResourceInvestmentSummary, ResourceWasteAnalysis

from .utils import convert_lead_code_to_project_code

router = APIRouter()


@router.get("/lead/{lead_id}/resource-investment", response_model=ResponseModel[ResourceInvestmentSummary])
async def get_lead_resource_investment(
    lead_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("presales_integration:create"))
) -> Any:
    """获取某线索/项目投入的资源工时"""

    project_code = convert_lead_code_to_project_code(lead_id) if lead_id.startswith('XS') else lead_id

    project = db.query(Project).filter(
        or_(
            Project.project_code == project_code,
            Project.source_lead_id == lead_id
        )
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail=f"未找到线索/项目: {lead_id}")

    from app.models.work_log import WorkLog

    work_logs = db.query(WorkLog).filter(WorkLog.project_id == project.id).all()

    total_hours = sum(log.work_hours or 0 for log in work_logs)
    engineer_ids = set(log.employee_id for log in work_logs if log.employee_id)

    engineer_hours = {}
    for log in work_logs:
        emp_id = log.employee_id
        if emp_id not in engineer_hours:
            engineer_hours[emp_id] = 0
        engineer_hours[emp_id] += log.work_hours or 0

    engineers = [
        {"employee_id": emp_id, "hours": hours}
        for emp_id, hours in engineer_hours.items()
    ]

    investment_by_month = {}
    for log in work_logs:
        month_key = log.work_date.strftime('%Y-%m') if log.work_date else 'unknown'
        if month_key not in investment_by_month:
            investment_by_month[month_key] = 0
        investment_by_month[month_key] += log.work_hours or 0

    hourly_rate = Decimal('300')
    estimated_cost = Decimal(str(total_hours)) * hourly_rate

    return ResponseModel(
        code=200,
        message="查询成功",
        data=ResourceInvestmentSummary(
            lead_id=lead_id,
            lead_name=project.name,
            total_hours=total_hours,
            engineer_hours=total_hours,
            presales_hours=0,
            design_hours=0,
            engineer_count=len(engineer_ids),
            engineers=engineers,
            estimated_cost=estimated_cost,
            hourly_rate=hourly_rate,
            investment_by_stage={},
            investment_by_month=investment_by_month
        )
    )


@router.get("/resource-waste-analysis", response_model=ResponseModel[ResourceWasteAnalysis])
async def get_resource_waste_analysis(
    period: str = Query(..., description="分析周期，格式 YYYY-MM 或 YYYY"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("presales_integration:create"))
) -> Any:
    """获取资源浪费分析报告"""

    if len(period) == 7:  # YYYY-MM
        year = int(period[:4])
        month = int(period[5:7])
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
    else:  # YYYY
        year = int(period)
        start_date = date(year, 1, 1)
        end_date = date(year + 1, 1, 1)

    projects = db.query(Project).filter(
        Project.created_at >= start_date,
        Project.created_at < end_date,
        Project.outcome.isnot(None)
    ).all()

    total_leads = len(projects)
    won_leads = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.WON.value)
    lost_leads = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.LOST.value)
    abandoned_leads = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.ABANDONED.value)
    pending_leads = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.PENDING.value)

    overall_win_rate = won_leads / (won_leads + lost_leads) if (won_leads + lost_leads) > 0 else 0

    from app.models.work_log import WorkLog

    total_investment_hours = 0
    wasted_hours = 0
    loss_reasons = {}

    for project in projects:
        project_hours = db.query(func.sum(WorkLog.work_hours)).filter(
            WorkLog.project_id == project.id
        ).scalar() or 0

        total_investment_hours += project_hours

        if project.outcome in [LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value]:
            wasted_hours += project_hours
            reason = project.loss_reason or 'OTHER'
            loss_reasons[reason] = loss_reasons.get(reason, 0) + 1

    hourly_rate = Decimal('300')
    wasted_cost = Decimal(str(wasted_hours)) * hourly_rate
    waste_rate = wasted_hours / total_investment_hours if total_investment_hours > 0 else 0

    return ResponseModel(
        code=200,
        message="分析成功",
        data=ResourceWasteAnalysis(
            analysis_period=period,
            total_leads=total_leads,
            won_leads=won_leads,
            lost_leads=lost_leads,
            abandoned_leads=abandoned_leads,
            pending_leads=pending_leads,
            overall_win_rate=round(overall_win_rate, 3),
            total_investment_hours=total_investment_hours,
            wasted_hours=wasted_hours,
            wasted_cost=wasted_cost,
            waste_rate=round(waste_rate, 3),
            loss_reasons=loss_reasons
        )
    )
