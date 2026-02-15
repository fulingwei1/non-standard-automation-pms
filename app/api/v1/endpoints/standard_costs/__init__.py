# -*- coding: utf-8 -*-
"""
标准成本库管理模块
"""

from fastapi import APIRouter

from . import crud, project_integration, bulk_import, history

router = APIRouter()

# 包含各个子路由
router.include_router(crud.router, tags=["标准成本-CRUD"])
router.include_router(project_integration.router, tags=["标准成本-项目集成"])
router.include_router(bulk_import.router, tags=["标准成本-批量导入"])
router.include_router(history.router, tags=["标准成本-历史记录"])

__all__ = ["router"]
