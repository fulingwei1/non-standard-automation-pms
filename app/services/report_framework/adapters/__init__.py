# -*- coding: utf-8 -*-
"""
报表适配器

用于将现有报表服务适配到统一报表框架
"""

from app.services.report_framework.adapters.acceptance import AcceptanceReportAdapter
from app.services.report_framework.adapters.base import BaseReportAdapter
from app.services.report_framework.adapters.meeting import MeetingReportAdapter
from app.services.report_framework.adapters.project import ProjectReportAdapter
from app.services.report_framework.adapters.template import TemplateReportAdapter
from app.services.report_framework.adapters.timesheet import TimesheetReportAdapter

__all__ = [
    "BaseReportAdapter",
    "AcceptanceReportAdapter",
    "TimesheetReportAdapter",
    "MeetingReportAdapter",
    "ProjectReportAdapter",
    "TemplateReportAdapter",
]
