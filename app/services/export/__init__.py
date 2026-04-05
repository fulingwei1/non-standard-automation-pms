# -*- coding: utf-8 -*-
"""
导出服务模块

提供文档导出相关的服务，包括：
- 水印服务
"""

from .watermark_service import (
    WatermarkConfig,
    WatermarkService,
    add_watermark_to_excel,
    add_watermark_to_pdf,
)

__all__ = [
    "WatermarkConfig",
    "WatermarkService",
    "add_watermark_to_pdf",
    "add_watermark_to_excel",
]
