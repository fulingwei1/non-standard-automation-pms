# -*- coding: utf-8 -*-
"""
成本管理服务模块

统一入口，提供所有成本相关服务的访问。
各子服务职责:
- cost_data_queries: 公共数据查询层（各服务共享）
- cost_dashboard_service: 成本仪表盘（看板数据聚合）
- cost_alert_service: 成本预警（预算执行检查）
- cost_forecast_service: 成本预测（趋势分析、线性/指数/历史预测）
- cost_overrun_analysis_service: 超支分析（原因、归责、影响）
- cost_prediction_service: AI成本预测（GLM-5模型）
- cost_service: 成本统一Facade（聚合分析与利润计算）
- cost_allocation_service: 费用分摊
- cost_collection_service: 成本自动归集
- cost_review_service: 成本复盘报告
- labor_cost_service: 工时成本计算
- labor_cost_utils: 工时成本辅助工具
"""

from app.services.cost.cost_alert_service import CostAlertService
from app.services.cost.cost_dashboard_service import CostDashboardService

# 公共数据查询层
from app.services.cost.cost_data_queries import (
    get_cost_by_type,
    get_month_cost_total,
    get_monthly_cost_data,
    get_project_actual_cost_from_records,
    get_project_budget_stats,
)
from app.services.cost.cost_forecast_service import CostForecastService
from app.services.cost.cost_overrun_analysis_service import CostOverrunAnalysisService
from app.services.cost.cost_prediction_service import CostPredictionService, GLM5CostPredictor

__all__ = [
    # 统一数据查询
    "get_project_budget_stats",
    "get_project_actual_cost_from_records",
    "get_monthly_cost_data",
    "get_month_cost_total",
    "get_cost_by_type",
    # 子服务
    "CostDashboardService",
    "CostAlertService",
    "CostForecastService",
    "CostOverrunAnalysisService",
    "CostPredictionService",
    "GLM5CostPredictor",
]
