# -*- coding: utf-8 -*-
"""
权限管理 API 模块
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .matrix import router as matrix_router

router = APIRouter()
router.include_router(matrix_router, tags=["权限管理"])
router.include_router(crud_router, tags=["权限管理"])
