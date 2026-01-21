# -*- coding: utf-8 -*-
"""
个人绩效模块

聚合所有个人绩效相关的路由
"""
from fastapi import APIRouter

from .my_performance import router as my_performance_router
from .trends import router as trends_router
from .user_performance import router as user_performance_router

router = APIRouter(
    prefix="/performance/individual",
    tags=["individual"]
)

# 聚合所有子路由
for route in my_performance_router.routes:
    router.routes.append(route)

for route in user_performance_router.routes:
    router.routes.append(route)

for route in trends_router.routes:
    router.routes.append(route)
