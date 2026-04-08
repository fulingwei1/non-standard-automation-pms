# -*- coding: utf-8 -*-
"""
Dashboard统计模块路由
这是一个兼容性文件，用于导入dashboard/stats.py中的路由
"""

from .dashboard.stats import router

# 导出路由以便在API路由器中使用
__all__ = ["router"]