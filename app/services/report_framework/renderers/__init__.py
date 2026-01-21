# -*- coding: utf-8 -*-
"""
渲染器模块

支持的导出格式：
- JsonRenderer: JSON 格式
- PdfRenderer: PDF 格式（使用 reportlab）
- ExcelRenderer: Excel 格式（使用 openpyxl）
- WordRenderer: Word 格式（使用 python-docx）
"""

from app.services.report_framework.renderers.base import Renderer, ReportResult, RenderError
from app.services.report_framework.renderers.json_renderer import JsonRenderer

__all__ = [
    "Renderer",
    "ReportResult",
    "RenderError",
    "JsonRenderer",
]
