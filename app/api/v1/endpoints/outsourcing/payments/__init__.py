# -*- coding: utf-8 -*-
"""
外协付款模块

聚合所有外协付款相关的路由
"""
from fastapi import APIRouter

from .crud import router as crud_router
from .print import router as print_router
from .statement import router as statement_router

router = APIRouter()

# 聚合所有子路由
for route in crud_router.routes:
    router.routes.append(route)

for route in print_router.routes:
    router.routes.append(route)

for route in statement_router.routes:
    router.routes.append(route)
