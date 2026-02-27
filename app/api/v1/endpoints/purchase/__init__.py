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

# 静态路径的子路由必须在动态路径(/{order_id})之前注册，避免被吞
# 采购申请（/requests）
router.include_router(requests_refactored_router, tags=["采购申请"])

# 收货单（/goods-receipts）
router.include_router(receipts_router, tags=["收货管理"])

# 审批工作流（/workflow）
router.include_router(workflow_router, tags=["采购审批工作流"])

# 采购订单（含 /{order_id} 动态路由，必须放最后）
router.include_router(orders_refactored_router, tags=["采购订单"])
