# -*- coding: utf-8 -*-
"""
奖金分配明细表模块

聚合所有分配明细表相关的路由
"""
from fastapi import APIRouter

from .crud import router as crud_router
from .download import router as download_router
from .operations import router as operations_router
from .rows import router as rows_router
from .template import router as template_router
from .upload import router as upload_router

router = APIRouter()

# 聚合所有子路由
for route in template_router.routes:
    router.routes.append(route)

for route in upload_router.routes:
    router.routes.append(route)

for route in crud_router.routes:
    router.routes.append(route)

for route in operations_router.routes:
    router.routes.append(route)

for route in download_router.routes:
    router.routes.append(route)

for route in rows_router.routes:
    router.routes.append(route)
