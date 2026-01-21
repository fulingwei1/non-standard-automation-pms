# -*- coding: utf-8 -*-
"""
统一审批系统 API 路由聚合
"""

from fastapi import APIRouter

from . import delegates, instances, pending, tasks, templates

router = APIRouter(prefix="/approvals", tags=["审批系统"])

# 模板管理
router.include_router(templates.router, prefix="/templates", tags=["审批模板"])

# 审批实例
router.include_router(instances.router, prefix="/instances", tags=["审批实例"])

# 审批任务操作
router.include_router(tasks.router, prefix="/tasks", tags=["审批任务"])

# 待办查询
router.include_router(pending.router, prefix="/pending", tags=["待办查询"])

# 代理人管理
router.include_router(delegates.router, prefix="/delegates", tags=["代理人管理"])
