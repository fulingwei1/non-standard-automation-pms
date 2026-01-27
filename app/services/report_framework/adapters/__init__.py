# -*- coding: utf-8 -*-
"""
报表适配器

用于将现有报表服务适配到统一报表框架
"""

from app.services.report_framework.adapters.acceptance import AcceptanceReportAdapter
from app.services.report_framework.adapters.analysis import (
    CostAnalysisAdapter,
    WorkloadAnalysisAdapter,
)
from app.services.report_framework.adapters.base import BaseReportAdapter
from app.services.report_framework.adapters.department import (
    DeptMonthlyAdapter,
    DeptReportAdapter,
    DeptWeeklyAdapter,
)
from app.services.report_framework.adapters.meeting import MeetingReportAdapter
from app.services.report_framework.adapters.project import (
    ProjectMonthlyAdapter,
    ProjectReportAdapter,
    ProjectWeeklyAdapter,
)
from app.services.report_framework.adapters.rd_expense import RdExpenseReportAdapter
from app.services.report_framework.adapters.report_data_generation import ReportDataGenerationAdapter
from app.services.report_framework.adapters.sales import SalesReportAdapter
from app.services.report_framework.adapters.template import TemplateReportAdapter
from app.services.report_framework.adapters.timesheet import TimesheetReportAdapter

__all__ = [
    "BaseReportAdapter",
    # 验收报表
    "AcceptanceReportAdapter",
    # 工时报表
    "TimesheetReportAdapter",
    # 会议报表
    "MeetingReportAdapter",
    # 项目报表
    "ProjectReportAdapter",
    "ProjectWeeklyAdapter",
    "ProjectMonthlyAdapter",
    # 部门报表
    "DeptReportAdapter",
    "DeptWeeklyAdapter",
    "DeptMonthlyAdapter",
    # 分析报表
    "WorkloadAnalysisAdapter",
    "CostAnalysisAdapter",
    # 销售报表
    "SalesReportAdapter",
    # 研发费用报表
    "RdExpenseReportAdapter",
    # 报表数据生成服务适配器
    "ReportDataGenerationAdapter",
    # 模板报表
    "TemplateReportAdapter",
]
