# -*- coding: utf-8 -*-
"""
发货单管理 API endpoints 聚合模块
"""

from fastapi import APIRouter

from . import crud, statistics

# 创建主路由
router = APIRouter()

# 聚合所有子模块的路由
router.include_router(crud.router)
router.include_router(statistics.router)
