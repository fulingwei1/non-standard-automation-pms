# -*- coding: utf-8 -*-
"""
预警统计模块

聚合所有预警统计相关的路由
"""
from fastapi import APIRouter

from .metrics import router as metrics_router
from .overview import router as overview_router
from .trends import router as trends_router

router = APIRouter(tags=["statistics"])

# 聚合所有子路由
for route in overview_router.routes:
    router.routes.append(route)

for route in trends_router.routes:
    router.routes.append(route)

for route in metrics_router.routes:
    router.routes.append(route)
