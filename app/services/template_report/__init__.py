# -*- coding: utf-8 -*-
"""
模板报表生成服务统一导出

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
from .company_reports import CompanyReportMixin
from .core import TemplateReportCore
from .dept_reports import DeptReportMixin
from .generic_report import GenericReportMixin
from .project_reports import ProjectReportMixin


class TemplateReportService(
    TemplateReportCore,
    ProjectReportMixin,
    DeptReportMixin,
    AnalysisReportMixin,
    CompanyReportMixin,
    GenericReportMixin,
):
    """
    模板报表生成服务（组合所有功能模块）

    ⚠️ 已废弃：请使用 app.services.report_framework.generators
    """

    def __init__(self):
        warnings.warn(
            "TemplateReportService 已废弃，请使用 app.services.report_framework.generators",
            DeprecationWarning,
            stacklevel=2,
        )


def _create_deprecated_service():
    """创建带废弃警告的单例"""
    warnings.warn(
        "template_report_service 已废弃，请使用 app.services.report_framework",
        DeprecationWarning,
        stacklevel=3,
    )
    # 返回一个不显示警告的实例（避免重复警告）
    service = object.__new__(TemplateReportService)
    return service


# 延迟创建单例，只在实际使用时警告
class _DeprecatedServiceProxy:
    """代理类，在访问时显示废弃警告"""

    _instance = None

    def __getattr__(self, name):
        if self._instance is None:
            warnings.warn(
                "template_report_service 已废弃，请使用 "
                "app.services.report_framework.generators 中的生成器",
                DeprecationWarning,
                stacklevel=2,
            )
            self._instance = TemplateReportService.__new__(TemplateReportService)
        return getattr(self._instance, name)


template_report_service = _DeprecatedServiceProxy()

__all__ = ["TemplateReportService", "template_report_service"]
