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

# 注册顺序很重要！具体路由必须在通用路由之前注册
# 否则 /machines/1/ 会被 /{bom_id} 匹配
router.include_router(machine_bom_router, prefix="/machines/{machine_id}")  # /machines/{machine_id}/
router.include_router(bom_items_router)  # /{bom_id}/items, /items/{item_id}
router.include_router(bom_release_router)  # /{bom_id}/release
router.include_router(bom_versions_router)  # /{bom_id}/versions
router.include_router(bom_export_router)  # /{bom_id}/export
router.include_router(bom_generate_router)  # /{bom_id}/generate-pr
router.include_router(bom_approve_router)  # /{bom_id}/approve
router.include_router(bom_detail_router)  # /{bom_id} - 必须放后面，避免捕获 /machines/{machine_id}
router.include_router(bom_import_router)  # /import
router.include_router(bom_templates_router)  # /templates
router.include_router(list_router)  # / - 必须放最后，避免捕获所有路径

__all__ = ["router"]
