# -*- coding: utf-8 -*-
"""
项目阶段视图模块路由聚合

通过直接合并所有子路由的 routes 来避免 FastAPI 的空路径限制。
"""
from fastapi import APIRouter

from . import pipeline, timeline, tree

# 创建主路由
router = APIRouter()

# 直接合并所有子路由的 routes（避免空路径问题）
for route in pipeline.router.routes:
    router.routes.append(route)
for route in timeline.router.routes:
    router.routes.append(route)
for route in tree.router.routes:
    router.routes.append(route)
