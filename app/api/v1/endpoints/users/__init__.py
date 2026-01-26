# -*- coding: utf-8 -*-
"""
用户管理模块

拆分自原 users.py (842行)，按功能域分为：
- models: 请求/响应模型
- utils: 辅助工具函数
- crud: 用户 CRUD 操作
- sync: 用户同步（员工同步、账号创建、状态管理）
- time_allocation: 工时分配统计
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .crud_refactored import router as crud_refactored_router
from .sync import router as sync_router
from .time_allocation import router as time_router

router = APIRouter()

# 用户 CRUD（使用重构版本，统一响应格式）
router.include_router(crud_refactored_router, tags=["用户管理"])
# 原版本保留作为参考
# router.include_router(crud_router, tags=["用户管理"])

# 用户同步
router.include_router(sync_router, tags=["用户同步"])

# 工时分配
router.include_router(time_router, tags=["工时分配"])
