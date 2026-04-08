# -*- coding: utf-8 -*-
"""
预售移动端模块路由
这是一个兼容性文件，用于导入presale/mobile.py中的路由
"""

from .presale.mobile import router

# 导出路由以便在API路由器中使用
__all__ = ["router"]