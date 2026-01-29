# -*- coding: utf-8 -*-
"""
售前管理 API - 模块化结构
"""

from fastapi import APIRouter

from .bids import router as bids_router
from .proposals import router as proposals_router
from .statistics import router as statistics_router
from .templates import router as templates_router
from .tickets import router as tickets_router

router = APIRouter()

router.include_router(tickets_router, prefix="/presale/tickets", tags=["presale-tickets"])
router.include_router(proposals_router)
router.include_router(templates_router)
router.include_router(bids_router, prefix="/presale", tags=["presale-bids"])
router.include_router(statistics_router)

__all__ = ['router']
