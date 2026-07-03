# -*- coding: utf-8 -*-
"""
销售预测（SALES-06 接线真算法）

- 公司整体预测：接线 SalesForecastService（真库数据：已签合同 + 漏斗加权 + 季节因子）。
- 团队/个人分解、准确性追踪、领导驾驶舱、增强预测族：原实现为整段硬编码演示数据
  且前端零调用，一律 501 下架——做实前不再对外吐假数据（同 MISC-01 止损口径）。
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

# ---------- 两个 router，分别对应注册时的不同 prefix ----------
# forecast_router: prefix="/forecast"；forecast_enhanced_router: prefix="/forecast-enhanced"
forecast_router = APIRouter()
forecast_enhanced_router = APIRouter()

_STOPGAP_DETAIL = (
    "该预测端点此前返回硬编码演示数据，已下架（SALES-06 止损）。"
    "公司整体预测请用 GET /sales/forecast/forecast/company-overview（真实数据）。"
)


def _not_implemented() -> Any:
    raise HTTPException(status_code=501, detail=_STOPGAP_DETAIL)


# ==================== 公司整体预测（真实现） ====================


@forecast_router.get("/forecast/company-overview", summary="公司整体销售预测")
def get_company_forecast(
    period: str = Query("quarterly", description="周期：monthly/quarterly/yearly"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """公司整体销售计划完成情况预测。

    基于真实数据：已签约合同（当期业绩）、漏斗各阶段商机 est_amount × 阶段赢单率、
    季节性因子与历史同期对比。由 SalesForecastService 计算，不再返回演示数据。
    """
    from app.services.sales_forecast_service import SalesForecastService

    return SalesForecastService(db).get_company_forecast(period=period)


# ==================== 以下端点硬编码演示数据已下架（501） ====================


@forecast_router.get("/forecast/team-breakdown", summary="团队销售预测分解（未实现）")
def get_team_forecast(
    period: str = Query("quarterly", description="周期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()


@forecast_router.get("/forecast/sales-rep-breakdown", summary="个人销售预测分解（未实现）")
def get_sales_rep_forecast(
    team_id: Optional[int] = Query(None, description="团队 ID"),
    period: str = Query("quarterly", description="周期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()


@forecast_router.get("/forecast/accuracy-tracking", summary="预测准确性追踪（未实现）")
def get_forecast_accuracy(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()


@forecast_router.get("/forecast/executive-dashboard", summary="领导驾驶舱（未实现）")
def get_executive_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()


@forecast_enhanced_router.get("/forecast/enhanced-prediction", summary="增强版销售预测（未实现）")
def get_enhanced_prediction(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()


@forecast_enhanced_router.get("/forecast/data-quality-score", summary="数据质量评分（未实现）")
def get_data_quality_score(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()


@forecast_enhanced_router.get("/forecast/activity-tracking", summary="销售动作追踪（未实现）")
def get_activity_tracking(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()


@forecast_enhanced_router.get("/forecast/accuracy-comparison", summary="预测准确性对比（未实现）")
def get_accuracy_comparison(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return _not_implemented()
