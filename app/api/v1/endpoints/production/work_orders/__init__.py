# -*- coding: utf-8 -*-
"""
工单管理模块路由聚合
"""
from fastapi import APIRouter

from . import assignment, crud, progress, status

# 创建主路由
router = APIRouter()

# 聚合所有子路由
router.include_router(crud.router, tags=["production-work-orders"])
router.include_router(assignment.router, tags=["production-work-orders"])
router.include_router(status.router, tags=["production-work-orders"])
router.include_router(progress.router, tags=["production-work-orders"])
