# -*- coding: utf-8 -*-
"""
客户管理模块

拆分自原 customers.py (392行)，按功能域分为：
- crud: 客户基本CRUD操作
- related: 关联数据查询
- view360: 客户360视图
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .crud_refactored import router as crud_refactored_router
from .related import router as related_router
from .view360 import router as view360_router

router = APIRouter()

# 客户CRUD（使用重构后的端点，使用通用CRUD路由生成器和统一响应格式）
router.include_router(crud_refactored_router, tags=["客户管理"])
# 原crud端点已重构，保留注释供参考：
# router.include_router(crud_router, tags=["客户管理"])

# 关联数据查询
router.include_router(related_router, tags=["客户关联"])

# 客户360视图
router.include_router(view360_router, tags=["客户360"])
