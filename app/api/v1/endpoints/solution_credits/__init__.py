# -*- coding: utf-8 -*-
"""
方案生成积分管理模块

拆分自原 solution_credits.py (460行)，按功能域分为：
- schemas: Schema定义
- user: 用户端API（查询积分、交易历史）
- admin: 管理员API（用户积分管理、配置管理）
- internal: 内部调用API（扣除/退还积分）
"""

from fastapi import APIRouter

from .admin import router as admin_router
from .internal import router as internal_router
from .user import router as user_router

router = APIRouter()

# 用户端API
router.include_router(user_router, tags=["积分-用户"])

# 管理员API
router.include_router(admin_router, tags=["积分-管理"])

# 内部调用API
router.include_router(internal_router, tags=["积分-内部"])
