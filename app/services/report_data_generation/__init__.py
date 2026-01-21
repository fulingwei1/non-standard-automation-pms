# -*- coding: utf-8 -*-
"""
报表数据生成服务统一导出

通过多重继承组合所有功能模块
"""

from .analysis_reports import AnalysisReportMixin
from .core import ReportDataGenerationCore
from .dept_reports import DeptReportMixin
from .project_reports import ProjectReportMixin
from .router import ReportRouterMixin


class ReportDataGenerationService(
    ReportDataGenerationCore,
    ProjectReportMixin,
    DeptReportMixin,
    AnalysisReportMixin,
    ReportRouterMixin,
):
    """报表数据生成服务（组合所有功能模块）"""

    def __init__(self):
        # 静态方法类，不需要初始化
        pass


# 创建单例
report_data_service = ReportDataGenerationService()

__all__ = [
    "ReportDataGenerationService",
    "report_data_service",
]
