# -*- coding: utf-8 -*-
"""
通知中心模块

拆分自原 notifications.py (335行)，按功能域分为：
- crud: 通知列表、已读标记、删除操作
- settings: 通知设置（用户偏好）
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .crud_refactored import router as crud_refactored_router
from .settings import router as settings_router

router = APIRouter()

# 通知CRUD操作（使用重构版本，统一响应格式）
router.include_router(crud_refactored_router, tags=["通知管理"])
# 原版本保留作为参考
# router.include_router(crud_router, tags=["通知管理"])

# 通知设置
router.include_router(settings_router, tags=["通知设置"])
