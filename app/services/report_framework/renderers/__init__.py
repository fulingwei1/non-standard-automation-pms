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

# 可选渲染器（需要额外依赖）
try:
    from app.services.report_framework.renderers.pdf_renderer import PdfRenderer
    __all__.append("PdfRenderer")
except ImportError:
    pass

try:
    from app.services.report_framework.renderers.excel_renderer import ExcelRenderer
    __all__.append("ExcelRenderer")
except ImportError:
    pass

try:
    from app.services.report_framework.renderers.word_renderer import WordRenderer
    __all__.append("WordRenderer")
except ImportError:
    pass
