# -*- coding: utf-8 -*-
"""
工程师管理 API 路由聚合
包含：项目管理、任务管理、进度更新、证明材料、延期报告、审批流程、进度可视化
"""

from fastapi import APIRouter

from app.api.v1.endpoints.engineers import (
    approvals,
    delays,
    progress,
    projects,
    proofs,
    tasks,
    visibility,
)

# 创建主路由
router = APIRouter()

# 注册子路由
router.include_router(projects.router, tags=["工程师-项目管理"])
router.include_router(tasks.router, tags=["工程师-任务管理"])
router.include_router(progress.router, tags=["工程师-进度管理"])
router.include_router(proofs.router, tags=["工程师-证明材料"])
router.include_router(delays.router, tags=["工程师-延期报告"])
router.include_router(approvals.router, tags=["工程师-审批流程"])
router.include_router(visibility.router, tags=["工程师-进度可视化"])


# 导出主路由供外部使用
__all__ = ["router"]
