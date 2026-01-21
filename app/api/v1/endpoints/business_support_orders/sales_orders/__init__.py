# -*- coding: utf-8 -*-
"""
销售订单管理模块路由聚合
"""
from fastapi import APIRouter

from . import crud, operations

# 创建主路由
router = APIRouter()

# 聚合所有子路由
router.include_router(crud.router, tags=["sales-orders"])
router.include_router(operations.router, tags=["sales-orders"])
