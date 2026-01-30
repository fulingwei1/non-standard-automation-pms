# -*- coding: utf-8 -*-
"""踩坑库 API 路由"""

from .crud_refactored import router as crud_refactored_router

# 使用重构版本，统一响应格式
router = crud_refactored_router
