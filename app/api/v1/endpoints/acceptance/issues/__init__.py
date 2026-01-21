# -*- coding: utf-8 -*-
"""
验收问题管理模块

聚合所有验收问题相关的路由
"""
from fastapi import APIRouter

from .crud import router as crud_router
from .follow_ups import router as follow_ups_router
from .operations import router as operations_router

router = APIRouter()

# 聚合所有子路由
for route in crud_router.routes:
    router.routes.append(route)

for route in operations_router.routes:
    router.routes.append(route)

for route in follow_ups_router.routes:
    router.routes.append(route)
