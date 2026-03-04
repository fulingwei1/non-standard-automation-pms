# -*- coding: utf-8 -*-
"""
项目模板配置 API
"""

from fastapi import APIRouter

from .apply import router as apply_router
from .crud import router as crud_router

router = APIRouter()

router.include_router(crud_router, prefix="/configs", tags=["template-configs"])
router.include_router(apply_router, prefix="/apply", tags=["template-apply"])

__all__ = ["router"]
