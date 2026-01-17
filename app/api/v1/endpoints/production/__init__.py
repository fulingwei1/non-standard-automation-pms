# -*- coding: utf-8 -*-
"""
生产管理模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter

from . import dashboard, plans, work_orders, work_reports, workshops, workstations

# 创建主路由
router = APIRouter()

# 聚合所有子路由（保持原有路由路径）
router.include_router(dashboard.router, tags=["production-dashboard"])
router.include_router(workshops.router, tags=["production-workshops"])
router.include_router(workstations.router, tags=["production-workstations"])
router.include_router(plans.router, tags=["production-plans"])
router.include_router(work_orders.router, tags=["production-work-orders"])
router.include_router(work_reports.router, tags=["production-work-reports"])
