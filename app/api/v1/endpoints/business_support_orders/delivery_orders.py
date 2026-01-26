# -*- coding: utf-8 -*-
"""
商务支持模块 - 发货管理 API endpoints

注意：此文件已拆分为多个模块，位于 delivery_orders/ 目录下
此文件仅用于向后兼容，重新导出路由
"""

from .delivery_orders import router

__all__ = ["router"]
