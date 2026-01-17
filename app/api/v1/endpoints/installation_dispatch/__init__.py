# -*- coding: utf-8 -*-
"""
安装调试派工模块

拆分自原 installation_dispatch.py (528行)，按功能域分为：
- utils: 辅助函数（generate_order_no）
- statistics: 派工统计
- orders: 派工单 CRUD
- workflow: 状态流转（派工、开始、进度、完成、取消）
"""

from fastapi import APIRouter

from .orders import router as orders_router
from .statistics import router as statistics_router
from .workflow import router as workflow_router

router = APIRouter()

# 统计路由
router.include_router(statistics_router, tags=["派工统计"])

# 派工单 CRUD
router.include_router(orders_router, tags=["安装调试派工"])

# 状态流转操作
router.include_router(workflow_router, tags=["派工流转"])
