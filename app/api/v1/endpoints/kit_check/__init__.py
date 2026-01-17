# -*- coding: utf-8 -*-
"""
齐套检查模块

拆分自原 kit_check.py (605行)，按功能域分为：
- utils: 编号生成和齐套率计算
- work_orders: 工单列表和齐套详情
- check: 执行检查和开工确认
- history: 检查历史查询
"""

from fastapi import APIRouter

from .check import router as check_router
from .history import router as history_router
from .work_orders import router as work_orders_router

router = APIRouter()

# 工单齐套查询
router.include_router(work_orders_router, tags=["工单齐套"])

# 齐套检查执行
router.include_router(check_router, tags=["齐套检查"])

# 检查历史
router.include_router(history_router, tags=["检查历史"])
