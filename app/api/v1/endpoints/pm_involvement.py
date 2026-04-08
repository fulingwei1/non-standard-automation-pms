# -*- coding: utf-8 -*-
"""
PM参与度模块路由
这是一个兼容性文件，用于导入performance/pm_involvement.py中的路由
"""

from .performance.pm_involvement import router

# 导出路由以便在API路由器中使用
__all__ = ["router"]