# -*- coding: utf-8 -*-
"""
模板报表生成服务统一导出

通过多重继承组合所有功能模块
"""

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
    """模板报表生成服务（组合所有功能模块）"""

    pass


# 创建单例
template_report_service = TemplateReportService()

__all__ = ["TemplateReportService", "template_report_service"]
