# -*- coding: utf-8 -*-
"""
知识库管理模块

聚合所有知识库相关的路由
"""
from fastapi import APIRouter

from .crud import router as crud_router
from .download import router as download_router
from .interactions import router as interactions_router
from .statistics import router as statistics_router
from .upload import router as upload_router

router = APIRouter()

# 聚合所有子路由
for route in statistics_router.routes:
    router.routes.append(route)

for route in crud_router.routes:
    router.routes.append(route)

for route in upload_router.routes:
    router.routes.append(route)

for route in download_router.routes:
    router.routes.append(route)

for route in interactions_router.routes:
    router.routes.append(route)
