# -*- coding: utf-8 -*-
"""
报表中心 API - 模块化结构
"""

from fastapi import APIRouter

from .bi import router as bi_router
from .configs import router as configs_router
from .generate import router as generate_router
from .rd_expense import router as rd_expense_router
from .templates import router as templates_router
from .unified import router as unified_router

router = APIRouter()

router.include_router(configs_router)
router.include_router(generate_router)
router.include_router(templates_router)
router.include_router(rd_expense_router)
router.include_router(bi_router)
router.include_router(unified_router)

__all__ = ['router']
