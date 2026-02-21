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

from .orders_refactored import router as orders_refactored_router
from .receipts import router as receipts_router
from .requests_refactored import router as requests_refactored_router
from .utils import generate_request_no
from .workflow import router as workflow_router

router = APIRouter()

# 采购订单（使用重构版本，统一响应格式）
router.include_router(orders_refactored_router, tags=["采购订单"])

# 采购申请（使用重构版本，统一响应格式）
router.include_router(requests_refactored_router, tags=["采购申请"])

# 收货单
router.include_router(receipts_router, tags=["收货管理"])

# 审批工作流（使用统一审批引擎）
router.include_router(workflow_router, tags=["采购审批工作流"])
