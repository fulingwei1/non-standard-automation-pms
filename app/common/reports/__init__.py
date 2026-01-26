# -*- coding: utf-8 -*-
"""
统一报表框架
提供统一的报表生成功能，支持配置驱动
"""

from app.common.reports.base import BaseReportGenerator
from app.common.reports.renderers import PDFRenderer, ExcelRenderer, WordRenderer

__all__ = [
    "BaseReportGenerator",
    "PDFRenderer",
    "ExcelRenderer",
    "WordRenderer",
]
