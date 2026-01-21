# -*- coding: utf-8 -*-
"""
齐套分析模块路由聚合

通过直接合并所有子路由的 routes 来避免 FastAPI 的空路径限制。
"""
from fastapi import APIRouter

from . import analysis, optimization, projects

# 创建主路由
router = APIRouter()

# 直接合并所有子路由的 routes（避免空路径问题）
for route in analysis.router.routes:
    router.routes.append(route)
for route in optimization.router.routes:
    router.routes.append(route)
for route in projects.router.routes:
    router.routes.append(route)
