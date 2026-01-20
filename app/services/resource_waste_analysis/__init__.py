# -*- coding: utf-8 -*-
"""
资源浪费分析服务统一导出

通过多重继承组合所有功能模块
"""

from sqlalchemy.orm import Session

from .core import ResourceWasteAnalysisCore
from .failure_patterns import FailurePatternsMixin
from .investment import InvestmentAnalysisMixin
from .report_generation import ReportGenerationMixin
from .salesperson_analysis import SalespersonAnalysisMixin
from .trends_comparison import TrendsComparisonMixin
from .waste_calculation import WasteCalculationMixin


class ResourceWasteAnalysisService(
    ResourceWasteAnalysisCore,
    InvestmentAnalysisMixin,
    WasteCalculationMixin,
    SalespersonAnalysisMixin,
    FailurePatternsMixin,
    TrendsComparisonMixin,
    ReportGenerationMixin,
):
    """资源浪费分析服务（组合所有功能模块）"""

    def __init__(self, db: Session, hourly_rate=None):
        ResourceWasteAnalysisCore.__init__(self, db, hourly_rate)


__all__ = ["ResourceWasteAnalysisService"]
