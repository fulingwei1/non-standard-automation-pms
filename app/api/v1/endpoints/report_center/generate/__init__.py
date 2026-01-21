# -*- coding: utf-8 -*-
"""
报表生成模块

聚合所有报表生成相关的路由
"""
from fastapi import APIRouter

from .comparison import router as comparison_router
from .download import router as download_router
from .export import router as export_router
from .generation import router as generation_router

router = APIRouter(
    prefix="/report-center/generate",
    tags=["generate"]
)

# 聚合所有子路由
for route in generation_router.routes:
    router.routes.append(route)

for route in comparison_router.routes:
    router.routes.append(route)

for route in export_router.routes:
    router.routes.append(route)

for route in download_router.routes:
    router.routes.append(route)
