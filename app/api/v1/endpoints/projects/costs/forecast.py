# -*- coding: utf-8 -*-
"""
项目成本预测模块

提供成本预测、趋势分析、燃尽图、预警等功能
路由: /projects/{project_id}/costs/forecast
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.cost_forecast_service import CostForecastService

router = APIRouter()


@router.get("/forecast", response_model=ResponseModel)
def get_project_cost_forecast(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    method: str = Query(
        "LINEAR",
        description="预测方法：LINEAR/EXPONENTIAL/HISTORICAL_AVERAGE",
    ),
    save_result: bool = Query(False, description="是否保存预测结果"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取项目成本预测

    支持3种预测方法：
    - LINEAR: 线性回归预测（基于历史数据的线性趋势）
    - EXPONENTIAL: 指数预测（适用于成本呈指数增长的项目）
    - HISTORICAL_AVERAGE: 历史平均法（基于历史月均成本）

    返回：
    - forecasted_completion_cost: 预测完工成本
    - monthly_forecast_data: 月度预测数据
    - trend_data: 趋势分析数据
    - is_over_budget: 是否超预算
    """
    service = CostForecastService(db)

    # 根据方法调用不同的预测算法
    if method == "LINEAR":
        result = service.linear_forecast(project_id)
    elif method == "EXPONENTIAL":
        result = service.exponential_forecast(project_id)
    elif method == "HISTORICAL_AVERAGE":
        result = service.historical_average_forecast(project_id)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的预测方法: {method}。支持的方法: LINEAR, EXPONENTIAL, HISTORICAL_AVERAGE",
        )

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    # 保存预测结果（可选）
    if save_result:
        service.save_forecast(project_id, result, current_user.id)

    return ResponseModel(code=200, message="预测成功", data=result)


@router.get("/trend", response_model=ResponseModel)
def get_project_cost_trend(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    start_month: Optional[str] = Query(None, description="开始月份（YYYY-MM）"),
    end_month: Optional[str] = Query(None, description="结束月份（YYYY-MM）"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取项目成本趋势

    返回月度成本趋势和累计成本趋势数据

    返回：
    - monthly_trend: 月度成本趋势 [{month, cost}]
    - cumulative_trend: 累计成本趋势 [{month, cumulative_cost}]
    - summary: 汇总统计（总月数、总成本、月均成本等）
    """
    service = CostForecastService(db)
    result = service.get_cost_trend(project_id, start_month, end_month)

    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])

    return ResponseModel(code=200, message="成功", data=result)


@router.get("/burn-down", response_model=ResponseModel)
def get_project_cost_burn_down(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取项目成本燃尽图数据

    燃尽图显示：
    - ideal_remaining: 理想剩余预算（基于预算和计划时间的均匀消耗）
    - actual_spent: 实际已花费成本
    - actual_remaining: 实际剩余预算

    返回：
    - budget: 项目预算
    - current_spent: 当前已花费
    - remaining_budget: 剩余预算
    - burn_rate: 燃烧率（月度）
    - burn_down_data: 燃尽图数据
    - is_on_track: 是否按计划进行
    """
    service = CostForecastService(db)
    result = service.get_burn_down_data(project_id)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return ResponseModel(code=200, message="成功", data=result)


@router.get("/alerts", response_model=ResponseModel)
def get_project_cost_alerts(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    auto_create: bool = Query(
        True, description="是否自动创建预警记录（检测到新预警时）"
    ),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取项目成本预警

    检测3类预警：
    1. OVERSPEND: 超支预警（实际成本 > 预算 × 阈值）
    2. PROGRESS_MISMATCH: 进度预警（完成度 vs 成本消耗比例不匹配）
    3. TREND_ANOMALY: 趋势预警（成本增长率异常）

    预警级别：
    - INFO: 信息提示
    - WARNING: 警告
    - CRITICAL: 严重

    返回：预警列表
    """
    service = CostForecastService(db)
    alerts = service.check_cost_alerts(project_id, auto_create=auto_create)

    return ResponseModel(
        code=200,
        message=f"检测到 {len(alerts)} 个预警",
        data={"alerts": alerts, "total_count": len(alerts)},
    )


@router.get("/forecast-history", response_model=ResponseModel)
def get_forecast_history(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    limit: int = Query(10, description="返回记录数"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取项目的历史预测记录

    用于对比不同时间点的预测结果，评估预测准确性
    """
    from app.models.project import CostForecast

    forecasts = (
        db.query(CostForecast)
        .filter(CostForecast.project_id == project_id)
        .order_by(CostForecast.forecast_date.desc())
        .limit(limit)
        .all()
    )

    result = []
    for forecast in forecasts:
        result.append(
            {
                "id": forecast.id,
                "forecast_date": forecast.forecast_date.isoformat(),
                "forecast_method": forecast.forecast_method,
                "forecasted_completion_cost": float(
                    forecast.forecasted_completion_cost
                ),
                "current_progress_pct": float(forecast.current_progress_pct or 0),
                "current_actual_cost": float(forecast.current_actual_cost or 0),
                "forecast_accuracy": (
                    float(forecast.forecast_accuracy)
                    if forecast.forecast_accuracy
                    else None
                ),
                "trend_data": forecast.trend_data,
            }
        )

    return ResponseModel(
        code=200, message="成功", data={"forecasts": result, "total_count": len(result)}
    )


@router.get("/compare-methods", response_model=ResponseModel)
def compare_forecast_methods(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    对比3种预测方法的结果

    帮助用户选择最适合的预测方法
    """
    service = CostForecastService(db)

    linear_result = service.linear_forecast(project_id)
    exponential_result = service.exponential_forecast(project_id)
    historical_result = service.historical_average_forecast(project_id)

    # 处理错误情况
    results = {
        "LINEAR": linear_result if not linear_result.get("error") else None,
        "EXPONENTIAL": (
            exponential_result if not exponential_result.get("error") else None
        ),
        "HISTORICAL_AVERAGE": (
            historical_result if not historical_result.get("error") else None
        ),
    }

    # 过滤掉错误的结果
    valid_results = {k: v for k, v in results.items() if v is not None}

    if not valid_results:
        raise HTTPException(status_code=400, detail="所有预测方法都失败了")

    # 对比汇总
    comparison = {
        "forecasted_costs": {
            method: result["forecasted_completion_cost"]
            for method, result in valid_results.items()
        },
        "data_points": {
            method: result.get("data_points", 0)
            for method, result in valid_results.items()
        },
        "is_over_budget": {
            method: result.get("is_over_budget", False)
            for method, result in valid_results.items()
        },
    }

    # 计算平均预测
    costs = list(comparison["forecasted_costs"].values())
    if costs:
        comparison["average_forecast"] = round(sum(costs) / len(costs), 2)
        comparison["min_forecast"] = round(min(costs), 2)
        comparison["max_forecast"] = round(max(costs), 2)
        comparison["forecast_range"] = round(max(costs) - min(costs), 2)

    return ResponseModel(
        code=200,
        message="对比成功",
        data={"methods": valid_results, "comparison": comparison},
    )
