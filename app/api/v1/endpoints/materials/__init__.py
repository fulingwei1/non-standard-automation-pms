# -*- coding: utf-8 -*-
"""
物料管理模块

拆分自原 materials.py (736行)，按功能域分为：
- crud: 物料CRUD
- categories: 物料分类
- suppliers: 供应商和物料供应商关联
- statistics: 仓储统计、物料替代、物料搜索
"""

from fastapi import APIRouter

from .categories import router as categories_router
from .crud_refactored import router as crud_refactored_router
from .statistics import router as statistics_router
from .suppliers import router as suppliers_router

router = APIRouter()

# 物料CRUD（使用重构后的端点，使用通用CRUD路由生成器和统一响应格式）
router.include_router(crud_refactored_router, tags=["物料管理"])

# 物料分类
router.include_router(categories_router, tags=["物料分类"])

# 供应商
router.include_router(suppliers_router, tags=["物料供应商"])

# 仓储统计和搜索
router.include_router(statistics_router, tags=["仓储统计"])
