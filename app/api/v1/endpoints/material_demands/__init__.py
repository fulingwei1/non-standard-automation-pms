# -*- coding: utf-8 -*-
"""
物料需求计划(MRP)模块

拆分自原 material_demands.py (481行)，按功能域分为：
- demands: 物料需求列表与库存对比
- generate: 自动生成采购需求
- schedule: 需求时间表
- forecast: 物料交期预测
"""

from fastapi import APIRouter

from .demands import router as demands_router
from .forecast import router as forecast_router
from .generate import router as generate_router
from .schedule import router as schedule_router

router = APIRouter()

# 物料需求列表与库存对比
router.include_router(demands_router, tags=["物料需求"])

# 自动生成采购需求
router.include_router(generate_router, tags=["采购需求生成"])

# 需求时间表
router.include_router(schedule_router, tags=["需求时间表"])

# 交期预测
router.include_router(forecast_router, tags=["交期预测"])
