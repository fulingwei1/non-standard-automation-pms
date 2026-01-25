# -*- coding: utf-8 -*-
"""
项目成员全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/members/

迁移指南：
    CRUD操作        -> /projects/{id}/members/
    冲突检查        -> /projects/{id}/members/conflicts
    批量添加        -> /projects/{id}/members/batch
    扩展操作        -> /projects/{id}/members/{mid}/notify-dept-manager
                   -> /projects/{id}/members/from-dept/{dept_id}

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

from .batch import router as batch_router
from .conflicts import router as conflicts_router
from .crud import router as crud_router
from .extended import router as extended_router

router = APIRouter()

# 保持兼容性的空路由聚合（所有子模块都已废弃）
router.include_router(crud_router, tags=["项目成员"])
router.include_router(conflicts_router, tags=["成员冲突"])
router.include_router(batch_router, tags=["成员批量"])
router.include_router(extended_router, tags=["成员扩展"])

__all__ = ["router"]
