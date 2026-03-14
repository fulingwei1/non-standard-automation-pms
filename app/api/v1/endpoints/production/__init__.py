# -*- coding: utf-8 -*-
"""
生产管理模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter

from . import (
    capacity,
    dashboard,
    exception_enhancement,
    exceptions,
    material_tracking,
    plans,
    progress,
    quality,
    schedule,
    work_orders,
    work_reports,
    workers,
    workshops,
    workstations,
)

# 创建主路由
router = APIRouter()

# 聚合所有子路由（保持原有路由路径）
router.include_router(dashboard.router, tags=["production-dashboard"])
router.include_router(workshops.router, tags=["production-workshops"])
router.include_router(workstations.router, tags=["production-workstations"])
router.include_router(workers.router, prefix="/workers", tags=["production-workers"])
router.include_router(plans.router, tags=["production-plans"])
router.include_router(work_orders.router, tags=["production-work-orders"])
router.include_router(work_reports.router, tags=["production-work-reports"])
router.include_router(exceptions.router, prefix="/exceptions", tags=["production-exceptions"])
router.include_router(
    material_tracking.router, prefix="/material", tags=["production-material-tracking"]
)
router.include_router(exception_enhancement.router, tags=["production-exception-enhancement"])
router.include_router(progress.router, prefix="/progress", tags=["production-progress-tracking"])
router.include_router(schedule.router, prefix="/schedule", tags=["production-schedule"])
router.include_router(quality.router, prefix="/quality", tags=["production-quality-management"])
router.include_router(capacity.router, prefix="/capacity", tags=["production-capacity-analysis"])
