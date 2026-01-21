# -*- coding: utf-8 -*-
"""
服务工单管理模块路由聚合

由于父路由已经设置了 /tickets 前缀，子路由使用相对路径。
通过直接合并所有子路由的 routes 来避免 FastAPI 的空路径限制。
"""
from fastapi import APIRouter

from . import assignment, crud, issues, statistics, status

# 创建主路由
router = APIRouter()

# 直接合并所有子路由的 routes（避免空路径问题）
for route in crud.router.routes:
    router.routes.append(route)
for route in statistics.router.routes:
    router.routes.append(route)
for route in assignment.router.routes:
    router.routes.append(route)
for route in status.router.routes:
    router.routes.append(route)
for route in issues.router.routes:
    router.routes.append(route)
