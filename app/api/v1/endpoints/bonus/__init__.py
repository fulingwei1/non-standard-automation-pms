# -*- coding: utf-8 -*-
"""
奖金管理 API - 模块化结构
"""

from fastapi import APIRouter

from .calculation import router as calculation_router
from .details import router as details_router
from .my_bonus import router as my_bonus_router
from .payment import router as payment_router
from .rules import router as rules_router
from .sales_calc import router as sales_calc_router
from .statistics import router as statistics_router
from .team import router as team_router

router = APIRouter()

router.include_router(rules_router)
router.include_router(calculation_router)
router.include_router(sales_calc_router)
router.include_router(payment_router)
router.include_router(team_router)
router.include_router(my_bonus_router)
router.include_router(statistics_router)
router.include_router(details_router)

__all__ = ['router']
