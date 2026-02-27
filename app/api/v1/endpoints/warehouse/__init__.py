# -*- coding: utf-8 -*-
"""仓储管理 API 模块"""
from fastapi import APIRouter
from .crud import router as crud_router
from .locations import router as locations_router
from .alerts import router as alerts_router
from .count import router as count_router

router = APIRouter()
router.include_router(crud_router, tags=["仓储-出入库"])
router.include_router(locations_router, tags=["仓储-库位"])
router.include_router(alerts_router, tags=["仓储-预警"])
router.include_router(count_router, tags=["仓储-盘点"])
