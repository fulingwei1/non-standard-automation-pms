# -*- coding: utf-8 -*-
"""
采购管理模块

拆分自原 purchase.py (738行)，按功能域分为：
- utils: 辅助函数（编号生成、序列化）
- orders: 采购订单CRUD
- requests: 采购申请CRUD
- receipts: 收货单CRUD
"""

from fastapi import APIRouter

from .orders import router as orders_router
from .receipts import router as receipts_router
from .requests import router as requests_router

router = APIRouter()

# 采购订单
router.include_router(orders_router, tags=["采购订单"])

# 采购申请
router.include_router(requests_router, tags=["采购申请"])

# 收货单
router.include_router(receipts_router, tags=["收货管理"])
