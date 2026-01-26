# -*- coding: utf-8 -*-
"""
项目阶段管理模块

路由: /projects/{project_id}/stages/
提供项目视角的阶段管理，核心功能由此处聚合。
"""

from fastapi import APIRouter

from . import (
    crud,
    stage_operations,
    node_operations,
    custom_nodes,
    node_assignment,
    status_updates,
    timeline,
    tree,
)

router = APIRouter()

# 聚合所有子模块路由
router.include_router(crud.router)
router.include_router(stage_operations.router, tags=["projects-stages-ops"])
router.include_router(node_operations.router, tags=["projects-nodes-ops"])
router.include_router(custom_nodes.router, tags=["projects-nodes-custom"])
router.include_router(node_assignment.router, tags=["projects-nodes-assignment"])
router.include_router(status_updates.router, tags=["projects-stages-status"])
router.include_router(timeline.router, tags=["projects-stages-views"])
router.include_router(tree.router, tags=["projects-stages-views"])

__all__ = ["router"]
