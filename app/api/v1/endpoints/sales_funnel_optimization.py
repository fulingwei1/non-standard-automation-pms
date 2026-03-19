# -*- coding: utf-8 -*-
"""
销售漏斗优化 API
提供转化率分析、瓶颈识别、预测准确性分析与健康度看板。
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services.sales.funnel_optimization_service import SalesFunnelOptimizationService

router = APIRouter()


@router.get("/conversion-rates", summary="销售漏斗转化率分析")
def get_funnel_conversion_rates(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    sales_id: Optional[int] = Query(None, description="销售 ID（为空则全部）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """分析销售漏斗各环节转化率。"""
    service = SalesFunnelOptimizationService(db)
    return service.get_conversion_rates(
        start_date=start_date,
        end_date=end_date,
        sales_id=sales_id,
        current_user=current_user,
    )


@router.get("/bottlenecks", summary="瓶颈识别")
def get_funnel_bottlenecks(
    threshold: float = Query(55.0, description="转化率阈值%（低于此值标红）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """识别销售漏斗中的瓶颈环节。"""
    service = SalesFunnelOptimizationService(db)
    return service.get_bottlenecks(
        threshold=threshold,
        current_user=current_user,
    )


@router.get("/prediction-accuracy", summary="预测准确性分析")
def get_prediction_accuracy(
    months: int = Query(3, description="分析月数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """分析赢单率预测的准确性。"""
    service = SalesFunnelOptimizationService(db)
    return service.get_prediction_accuracy(
        months=months,
        current_user=current_user,
    )


@router.get("/health-dashboard", summary="漏斗健康度仪表盘")
def get_funnel_health_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """销售漏斗整体健康度评估。"""
    service = SalesFunnelOptimizationService(db)
    return service.get_health_dashboard(current_user=current_user)


@router.get("/trends", summary="销售趋势分析")
def get_funnel_trends(
    period: str = Query("monthly", description="周期：daily/weekly/monthly"),
    months: int = Query(6, description="分析月数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """销售漏斗趋势分析。"""
    service = SalesFunnelOptimizationService(db)
    return service.get_trends(
        period=period,
        months=months,
        current_user=current_user,
    )
