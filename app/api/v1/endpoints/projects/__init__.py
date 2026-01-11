# -*- coding: utf-8 -*-
"""
项目管理模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter
from . import core, status, payment_plans, templates, cache, archive, extended

# 创建主路由
router = APIRouter()

# 聚合所有子路由（保持原有路由路径）
# 注意：路由的顺序很重要，更具体的路由应该放在前面

# 模板路由（放在最前面，避免与/{project_id}冲突）
router.include_router(templates.router, tags=["projects-templates"])

# 缓存管理路由
router.include_router(cache.router, tags=["projects-cache"])

# 归档管理路由
router.include_router(archive.router, tags=["projects-archive"])

# 核心CRUD路由
router.include_router(core.router, tags=["projects-core"])

# 状态管理路由
router.include_router(status.router, tags=["projects-status"])

# 付款计划路由
router.include_router(payment_plans.router, tags=["projects-payment-plans"])

# 扩展功能路由（复盘、经验教训、最佳实践、数据同步、ERP集成等）
router.include_router(extended.router, tags=["projects-extended"])
