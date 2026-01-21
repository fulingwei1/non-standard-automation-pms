# -*- coding: utf-8 -*-
"""
采购分析服务

统一导出服务类
"""
from .base import ProcurementAnalysisService

# 创建单例
procurement_analysis_service = ProcurementAnalysisService()

__all__ = ["ProcurementAnalysisService", "procurement_analysis_service"]
