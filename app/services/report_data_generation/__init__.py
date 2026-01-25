# -*- coding: utf-8 -*-
"""
报表数据生成服务统一导出

⚠️ 已废弃 (DEPRECATED)
此模块已被 app.services.report_framework 取代。
请使用统一报表框架中的生成器和适配器：

    # 新的用法
    from app.services.report_framework.generators import (
        ProjectReportGenerator,
        DeptReportGenerator,
        AnalysisReportGenerator,
    )
    from app.services.report_framework.adapters import (
        ProjectWeeklyAdapter,
        ProjectMonthlyAdapter,
        DeptWeeklyAdapter,
        DeptMonthlyAdapter,
        WorkloadAnalysisAdapter,
        CostAnalysisAdapter,
    )

此模块将在未来版本中移除。
"""

import warnings

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
    """
    报表数据生成服务（组合所有功能模块）

    ⚠️ 已废弃：请使用 app.services.report_framework.generators
    """

    def __init__(self):
        warnings.warn(
            "ReportDataGenerationService 已废弃，请使用 "
            "app.services.report_framework.generators",
            DeprecationWarning,
            stacklevel=2,
        )


# 延迟创建单例，只在实际使用时警告
class _DeprecatedServiceProxy:
    """代理类，在访问时显示废弃警告"""

    _instance = None

    def __getattr__(self, name):
        if self._instance is None:
            warnings.warn(
                "report_data_service 已废弃，请使用 "
                "app.services.report_framework.generators 中的生成器",
                DeprecationWarning,
                stacklevel=2,
            )
            self._instance = ReportDataGenerationService.__new__(
                ReportDataGenerationService
            )
        return getattr(self._instance, name)


report_data_service = _DeprecatedServiceProxy()

__all__ = [
    "ReportDataGenerationService",
    "report_data_service",
]
