# -*- coding: utf-8 -*-
"""
格式化器模块

内置格式化器：
- status_badge: 状态徽章
- percentage: 百分比格式
- currency: 货币格式
- date_format: 日期格式化
"""

from app.services.report_framework.formatters.builtin import (
    format_status_badge,
    format_percentage,
    format_currency,
    format_date,
)

__all__ = [
    "format_status_badge",
    "format_percentage",
    "format_currency",
    "format_date",
]
