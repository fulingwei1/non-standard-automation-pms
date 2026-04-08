# -*- coding: utf-8 -*-
"""
采购分析模块路由
这是一个兼容性文件，用于导入procurement/analysis.py中的路由
"""

from .procurement.analysis import router

# 导出路由以便在API路由器中使用
__all__ = ["router"]