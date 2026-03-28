# -*- coding: utf-8 -*-
"""
项目交付排产计划 API
"""

from fastapi import APIRouter

from . import schedules, tasks, purchases, designs, changes, gantt

router = APIRouter()

# 注册子路由
router.include_router(schedules.router, prefix="/schedules", tags=["project-delivery-schedules"])
router.include_router(tasks.router, prefix="/schedules", tags=["project-delivery-tasks"])
router.include_router(purchases.router, prefix="/schedules", tags=["project-delivery-purchases"])
router.include_router(designs.router, prefix="/schedules", tags=["project-delivery-designs"])
router.include_router(changes.router, prefix="/schedules", tags=["project-delivery-changes"])
router.include_router(gantt.router, prefix="/schedules", tags=["project-delivery-gantt"])

__all__ = ["router"]
