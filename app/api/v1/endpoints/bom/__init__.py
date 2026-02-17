# -*- coding: utf-8 -*-
"""
BOM 管理 API - 模块化结构
"""

from fastapi import APIRouter

from .bom_approve import router as bom_approve_router
from .bom_detail import router as bom_detail_router
from .bom_export import router as bom_export_router
from .bom_generate import router as bom_generate_router
from .bom_import import router as bom_import_router
from .bom_items import router as bom_items_router
from .bom_release import router as bom_release_router
from .bom_templates import router as bom_templates_router
from .bom_versions import router as bom_versions_router
from .list import router as list_router
from .machine_bom import router as machine_bom_router

router = APIRouter()

router.include_router(list_router)
router.include_router(machine_bom_router, prefix="/machines/{machine_id}")
router.include_router(bom_detail_router)
router.include_router(bom_items_router)
router.include_router(bom_release_router)
router.include_router(bom_versions_router)
router.include_router(bom_import_router)
router.include_router(bom_export_router)
router.include_router(bom_templates_router)
router.include_router(bom_generate_router)
router.include_router(bom_approve_router)

__all__ = ["router"]
