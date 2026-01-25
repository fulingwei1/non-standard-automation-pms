# -*- coding: utf-8 -*-
"""
发票管理 API 路由聚合
"""

from fastapi import APIRouter

from ...approvals import router as approvals_router
from .basic import router as basic_router
from .export import router as export_router
from .legacy import router as legacy_router
from .operations import router as operations_router
from .workflow import router as workflow_router

router = APIRouter()

# 基础 CRUD 路由
router.include_router(basic_router)

# 发票操作路由
router.include_router(operations_router)

# 多级审批路由（旧版）
router.include_router(approvals_router)

# 工作流审批路由（新版）
router.include_router(workflow_router)

# 导出功能路由
router.include_router(export_router)

# 兼容旧版路由
router.include_router(legacy_router)

__all__ = ["router"]
