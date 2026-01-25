# -*- coding: utf-8 -*-
"""
机台管理全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/machines/

迁移指南：
    CRUD操作        -> /projects/{id}/machines/
    文档管理        -> /projects/{id}/machines/{mid}/documents/
    服务历史        -> /projects/{id}/machines/{mid}/service-history

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .documents import router as documents_router
from .service_history import router as service_history_router

router = APIRouter()

# 保持兼容性的空路由聚合（所有子模块都已废弃）
router.include_router(crud_router, tags=["机台管理"])
router.include_router(service_history_router, tags=["设备档案"])
router.include_router(documents_router, tags=["机台文档"])

__all__ = ["router"]
