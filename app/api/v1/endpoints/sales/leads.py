# -*- coding: utf-8 -*-
"""
线索管理 API endpoints

注意：此文件已拆分为多个模块，位于 leads/ 目录下
此文件仅用于向后兼容，重新导出路由
"""

from .leads import router

__all__ = ["router"]
