# -*- coding: utf-8 -*-
"""
统一审批系统 API 路由聚合
"""

from fastapi import APIRouter

from . import delegates, instances, pending_refactored, tasks, templates

# 创建主路由（不在root level设置prefix，允许作为子路由使用）
router = APIRouter()

# 模板管理
router.include_router(templates.router, prefix="/templates", tags=["审批模板"])

# 审批实例
router.include_router(instances.router, prefix="/instances", tags=["审批实例"])

# 审批任务操作
router.include_router(tasks.router, prefix="/tasks", tags=["审批任务"])

# 待办查询（使用重构版本，统一响应格式）
router.include_router(pending_refactored.router, prefix="/pending", tags=["待办查询"])

# 代理人管理
router.include_router(delegates.router, prefix="/delegates", tags=["代理人管理"])
