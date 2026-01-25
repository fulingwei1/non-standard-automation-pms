# -*- coding: utf-8 -*-
"""
项目评价全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，请使用项目中心端点。

详见 project_evaluation/__init__.py
"""

from .project_evaluation import router

__all__ = ["router"]
