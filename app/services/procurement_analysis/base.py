# -*- coding: utf-8 -*-
"""
采购分析服务 - 基础类
"""
from .cost_trend import CostTrendAnalyzer
from .delivery_performance import DeliveryPerformanceAnalyzer
from .price_analysis import PriceAnalyzer
from .quality_analysis import QualityAnalyzer
from .request_efficiency import RequestEfficiencyAnalyzer


class ProcurementAnalysisService:
    """采购分析服务类"""

    # 向后兼容：将子模块静态方法暴露为服务类静态方法
    @staticmethod
    def get_cost_trend_data(*args, **kwargs):
        return CostTrendAnalyzer.get_cost_trend_data(*args, **kwargs)

    @staticmethod
    def get_price_fluctuation_data(*args, **kwargs):
        return PriceAnalyzer.get_price_fluctuation_data(*args, **kwargs)

    @staticmethod
    def get_delivery_performance_data(*args, **kwargs):
        return DeliveryPerformanceAnalyzer.get_delivery_performance_data(*args, **kwargs)

    @staticmethod
    def get_request_efficiency_data(*args, **kwargs):
        return RequestEfficiencyAnalyzer.get_request_efficiency_data(*args, **kwargs)

    @staticmethod
    def get_quality_rate_data(*args, **kwargs):
        return QualityAnalyzer.get_quality_rate_data(*args, **kwargs)
