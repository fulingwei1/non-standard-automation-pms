# -*- coding: utf-8 -*-
"""
统一报表数据生成器

整合原有 template_report 和 report_data_generation 中的重复逻辑
"""

from app.services.report_framework.generators.project import ProjectReportGenerator
from app.services.report_framework.generators.department import DeptReportGenerator
from app.services.report_framework.generators.analysis import AnalysisReportGenerator

__all__ = [
    "ProjectReportGenerator",
    "DeptReportGenerator",
    "AnalysisReportGenerator",
]
