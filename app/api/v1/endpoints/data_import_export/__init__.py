# -*- coding: utf-8 -*-
"""
数据导入导出 API - 模块化结构
"""

from fastapi import APIRouter

from .export_projects import router as export_projects_router
from .export_tasks import router as export_tasks_router
from .export_timesheet import router as export_timesheet_router
from .export_workload import router as export_workload_router
from .import_preview import router as import_preview_router
from .import_upload import router as import_upload_router
from .import_validate import router as import_validate_router
from .templates import router as templates_router

router = APIRouter()

router.include_router(templates_router, tags=["templates"])
router.include_router(import_preview_router, tags=["import"])
router.include_router(import_validate_router, tags=["import"])
router.include_router(import_upload_router, tags=["import"])
router.include_router(export_projects_router, tags=["export"])
router.include_router(export_tasks_router, tags=["export"])
router.include_router(export_timesheet_router, tags=["export"])
router.include_router(export_workload_router, tags=["export"])

__all__ = ["router"]
