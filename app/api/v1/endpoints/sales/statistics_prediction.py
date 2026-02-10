# -*- coding: utf-8 -*-
"""
销售统计 - 预测功能

包含收入预测、销售预测、预测准确率评估
"""

from datetime import date

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.date_range import get_month_range
from app.core import security
from app.models.sales import Opportunity
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.sales_prediction_service import SalesPredictionService

router = APIRouter()


@router.get("/statistics/revenue-forecast", response_model=ResponseModel)
def get_revenue_forecast(
    db: Session = Depends(deps.get_db),
    months: int = Query(3, ge=1, le=12, description="预测月数"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    收入预测（基于已签订合同和进行中的商机）
    """
    from datetime import timedelta

    today = date.today()
    forecast = []

    for i in range(months):
        forecast_date = today + timedelta(days=30 * (i + 1))
        month_start_date, month_end_date = get_month_range(forecast_date)

        # 统计该月预计签约的合同金额（基于商机预计金额）
        opps_in_month = (
            db.query(Opportunity)
            .filter(Opportunity.stage.in_(["PROPOSAL", "NEGOTIATION"]))
            .all()
        )

        # 简化处理：假设进行中的商机在接下来几个月平均分布
        estimated_revenue = sum([float(opp.est_amount or 0) for opp in opps_in_month]) / months

        forecast.append({
            "month": forecast_date.strftime("%Y-%m"),
            "estimated_revenue": round(estimated_revenue, 2)
        })

    return ResponseModel(code=200, message="success", data={"forecast": forecast})


@router.get("/statistics/prediction", response_model=ResponseModel)
def get_sales_prediction(
    *,
    db: Session = Depends(deps.get_db),
    days: int = Query(90, ge=30, le=365, description="预测天数（30/60/90）"),
    method: str = Query("moving_average", description="预测方法：moving_average/exponential_smoothing"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 6.3: 销售预测增强
    使用移动平均法或指数平滑法进行收入预测
    """
    service = SalesPredictionService(db)
    prediction = service.predict_revenue(
        days=days,
        method=method,
        customer_id=customer_id,
        owner_id=owner_id,
    )

    return ResponseModel(
        code=200,
        message="success",
        data=prediction
    )


@router.get("/statistics/prediction/accuracy", response_model=ResponseModel)
def get_prediction_accuracy(
    *,
    db: Session = Depends(deps.get_db),
    days_back: int = Query(90, ge=30, le=365, description="评估时间段（天数）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 6.3: 预测准确度评估
    对比历史预测值和实际值
    """
    service = SalesPredictionService(db)
    accuracy = service.evaluate_prediction_accuracy(days_back=days_back)

    return ResponseModel(
        code=200,
        message="success",
        data=accuracy
    )
