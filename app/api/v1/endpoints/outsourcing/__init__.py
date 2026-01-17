# -*- coding: utf-8 -*-
"""
外协管理 API - 模块化结构
"""

from fastapi import APIRouter

from .deliveries import router as deliveries_router
from .orders import router as orders_router
from .payments import router as payments_router
from .progress import router as progress_router
from .quality import router as quality_router
from .suppliers import router as suppliers_router

router = APIRouter()

router.include_router(suppliers_router)
router.include_router(orders_router)
router.include_router(deliveries_router)
router.include_router(quality_router)
router.include_router(progress_router)
router.include_router(payments_router)

__all__ = ['router']
