# -*- coding: utf-8 -*-
"""
项目角色全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，请使用项目中心端点。

详见 project_roles/__init__.py
"""

from .project_roles import router

__all__ = ["router"]
