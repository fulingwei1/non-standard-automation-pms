# -*- coding: utf-8 -*-
"""
成本预测服务 - 重新导出模块

此模块重新导出 cost 子目录中的成本预测服务，
用于向后兼容。
"""

from app.services.cost.cost_forecast_service import (
    CostForecastService,
)

__all__ = [
    "CostForecastService",
]