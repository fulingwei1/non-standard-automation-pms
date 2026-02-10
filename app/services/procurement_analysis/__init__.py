# -*- coding: utf-8 -*-
"""
采购分析服务

统一导出服务类
"""
from .base import ProcurementAnalysisService
from .price_analysis import PriceAnalyzer
from .cost_trend import CostTrendAnalyzer
from .delivery_performance import DeliveryPerformanceAnalyzer
from .request_efficiency import RequestEfficiencyAnalyzer
from .quality_analysis import QualityAnalyzer

# 创建单例
procurement_analysis_service = ProcurementAnalysisService()

__all__ = [
    "ProcurementAnalysisService",
    "procurement_analysis_service",
    "PriceAnalyzer",
    "CostTrendAnalyzer",
    "DeliveryPerformanceAnalyzer",
    "RequestEfficiencyAnalyzer",
    "QualityAnalyzer",
]
