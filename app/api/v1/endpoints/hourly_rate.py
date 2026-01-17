# -*- coding: utf-8 -*-
"""
时薪配置管理 API

已拆分为模块化结构，详见 hourly_rate/ 目录：
- crud.py: 时薪配置CRUD操作
- query.py: 时薪查询API
"""

from .hourly_rate import router

__all__ = ["router"]
