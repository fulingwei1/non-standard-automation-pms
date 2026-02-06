# -*- coding: utf-8 -*-
"""
商机管理 - 分析和导出
"""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import OpportunityStageEnum
from app.models.project import Customer
from app.models.sales import Opportunity
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/opportunities/funnel", response_model=ResponseModel)
def get_opportunity_funnel(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    商机漏斗统计
    按阶段统计商机数量和金额，计算转化率
    """
    query = db.query(Opportunity)

    if start_date:
        query = query.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))
    if owner_id:
        query = query.filter(Opportunity.owner_id == owner_id)

    stages = [stage.value for stage in OpportunityStageEnum]
    funnel_data = {}
    total_count = 0
    total_amount = 0

    for stage in stages:
        stage_query = query.filter(Opportunity.stage == stage)
        count = stage_query.count()
        amount_query = db.query(func.sum(Opportunity.est_amount)).filter(Opportunity.stage == stage)
        if start_date:
            amount_query = amount_query.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            amount_query = amount_query.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))
        if owner_id:
            amount_query = amount_query.filter(Opportunity.owner_id == owner_id)
        amount_result = amount_query.scalar() or 0

        funnel_data[stage] = {
            "count": count,
            "total_amount": float(amount_result),
            "avg_amount": float(amount_result / count) if count > 0 else 0
        }
        total_count += count
        total_amount += float(amount_result)

    # 计算转化率（从前一阶段到当前阶段）
    conversion_rates = {}
    prev_count = None
    for stage in stages:
        current_count = funnel_data[stage]["count"]
        if prev_count is not None and prev_count > 0:
            conversion_rates[stage] = round((current_count / prev_count) * 100, 2)
        else:
            conversion_rates[stage] = 100.0 if current_count > 0 else 0.0
        prev_count = current_count

    return ResponseModel(
        code=200,
        message="success",
        data={
            "funnel": funnel_data,
            "conversion_rates": conversion_rates,
            "total_count": total_count,
            "total_amount": total_amount
        }
    )


@router.get("/opportunities/{opp_id}/win-probability", response_model=ResponseModel)
def get_opportunity_win_probability(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 6.3: 商机赢单概率预测
    基于商机阶段、金额、历史赢单率
    """
    from app.services.sales_prediction_service import SalesPredictionService

    service = SalesPredictionService(db)
    probability = service.predict_win_probability(opportunity_id=opp_id)

    return ResponseModel(
        code=200,
        message="success",
        data=probability
    )


@router.get("/opportunities/export")
def export_opportunities(
    *,
    db: Session = Depends(deps.get_db),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    stage: Optional[str] = Query(None, description="阶段筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.2: 导出商机列表（Excel）
    """
    from app.services.excel_export_service import (
        ExcelExportService,
        create_excel_response,
    )

    query = db.query(Opportunity)
    if keyword:
        query = query.filter(or_(Opportunity.opp_code.contains(keyword), Opportunity.opp_name.contains(keyword), Opportunity.customer.has(Customer.customer_name.contains(keyword))))
    if stage:
        query = query.filter(Opportunity.stage == stage)
    if status:
        query = query.filter(Opportunity.gate_status == status)
    if owner_id:
        query = query.filter(Opportunity.owner_id == owner_id)

    opportunities = query.order_by(Opportunity.created_at.desc()).all()
    export_service = ExcelExportService()
    columns = [
        {"key": "opp_code", "label": "商机编码", "width": 15},
        {"key": "opp_name", "label": "商机名称", "width": 30},
        {"key": "customer_name", "label": "客户名称", "width": 25},
        {"key": "stage", "label": "阶段", "width": 15},
        {"key": "est_amount", "label": "预估金额", "width": 15, "format": export_service.format_currency},
        {"key": "est_margin", "label": "预估毛利率", "width": 12, "format": export_service.format_percentage},
        {"key": "score", "label": "评分", "width": 8},
        {"key": "risk_level", "label": "风险等级", "width": 10},
        {"key": "owner_name", "label": "负责人", "width": 12},
        {"key": "gate_status", "label": "阶段门状态", "width": 15},
        {"key": "created_at", "label": "创建时间", "width": 18, "format": export_service.format_date},
    ]

    data = [{
        "opp_code": opp.opp_code,
        "opp_name": opp.opp_name,
        "customer_name": opp.customer.customer_name if opp.customer else '',
        "stage": opp.stage,
        "est_amount": float(opp.est_amount) if opp.est_amount else 0,
        "est_margin": float(opp.est_margin) if opp.est_margin else 0,
        "score": opp.score or 0,
        "risk_level": opp.risk_level or '',
        "owner_name": opp.owner.real_name if opp.owner else '',
        "gate_status": opp.gate_status,
        "created_at": opp.created_at,
    } for opp in opportunities]

    excel_data = export_service.export_to_excel(data=data, columns=columns, sheet_name="商机列表", title="商机列表")
    filename = f"商机列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return create_excel_response(excel_data, filename)
