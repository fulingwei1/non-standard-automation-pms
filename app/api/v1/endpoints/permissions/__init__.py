# -*- coding: utf-8 -*-
"""
权限管理 API 模块
"""

from fastapi import APIRouter

from .matrix import router as matrix_router

router = APIRouter()
router.include_router(matrix_router, prefix="/permissions", tags=["权限管理"])
