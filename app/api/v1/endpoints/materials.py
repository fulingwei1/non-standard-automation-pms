# -*- coding: utf-8 -*-
"""
物料管理 API endpoints

已拆分为模块化结构，详见 materials/ 目录：
- crud.py: 物料CRUD
- categories.py: 物料分类
- suppliers.py: 供应商和物料供应商关联
- statistics.py: 仓储统计、物料替代、物料搜索
"""

from .materials import router

__all__ = ["router"]
