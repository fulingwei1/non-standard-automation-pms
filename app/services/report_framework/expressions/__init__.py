# -*- coding: utf-8 -*-
"""
表达式引擎模块

基于 Jinja2 实现动态值计算：
- parser: Jinja2 环境配置
- filters: 自定义过滤器
"""

from app.services.report_framework.expressions.parser import ExpressionParser, ExpressionError
from app.services.report_framework.expressions.filters import register_filters

__all__ = [
    "ExpressionParser",
    "ExpressionError",
    "register_filters",
]
