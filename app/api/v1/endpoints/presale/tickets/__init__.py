# -*- coding: utf-8 -*-
"""
售前工单管理模块路由聚合

通过直接合并所有子路由的 routes 来避免 FastAPI 的空路径限制。
"""
from fastapi import APIRouter

from . import board, crud, operations

# 创建主路由（不设置 prefix，由父路由处理）
router = APIRouter()

# 直接合并所有子路由的 routes（避免空路径问题）
for route in crud.router.routes:
    router.routes.append(route)
for route in operations.router.routes:
    router.routes.append(route)
for route in board.router.routes:
    router.routes.append(route)
