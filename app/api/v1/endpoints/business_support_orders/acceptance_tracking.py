# -*- coding: utf-8 -*-
"""
商务支持模块 - 验收单跟踪 API endpoints - 路由聚合

已拆分为模块化结构：
- tracking_crud.py: 基础CRUD操作（list, get, create, update）
- tracking_operations.py: 操作功能（check_condition, remind）
- tracking_helpers.py: 辅助函数（响应构建）
"""

from fastapi import APIRouter

from . import tracking_crud, tracking_operations

router = APIRouter()

# 聚合所有子路由
router.include_router(tracking_crud.router)
router.include_router(tracking_operations.router)
