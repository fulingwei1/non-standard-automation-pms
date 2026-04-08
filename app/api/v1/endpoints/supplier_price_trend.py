# -*- coding: utf-8 -*-
"""
供应商价格趋势模块路由
这是一个兼容性文件，用于导入procurement/supplier_price_trend.py中的路由
"""

from .procurement.supplier_price_trend import router

# 导出路由以便在API路由器中使用
__all__ = ["router"]