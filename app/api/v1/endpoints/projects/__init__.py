# -*- coding: utf-8 -*-
"""
项目管理模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中

拆分记录：
- core.py: 项目核心CRUD
- status.py: 项目状态管理
- payment_plans.py: 付款计划
- templates.py: 项目模板
- cache.py: 缓存管理
- archive.py: 归档管理
- dashboard.py: 概览和仪表盘
- sync.py: 数据同步和ERP集成
- reviews.py: 项目复盘管理
- lessons.py: 经验教训管理
- best_practices.py: 最佳实践管理
- analysis.py: 高级分析（资源优化、关联分析、风险矩阵等）
- costs.py: 项目成本和概览
- extended.py: 兼容层（已拆分）
"""

from fastapi import APIRouter
from . import (
    core, status, payment_plans, templates, cache, archive,
    dashboard, sync, reviews, lessons, best_practices, analysis, costs
)

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

# 概览和仪表盘路由
router.include_router(dashboard.router, tags=["projects-dashboard"])

# 数据同步和ERP集成路由
router.include_router(sync.router, tags=["projects-sync"])

# 项目复盘管理路由
router.include_router(reviews.router, tags=["projects-reviews"])

# 经验教训管理路由
router.include_router(lessons.router, tags=["projects-lessons"])

# 最佳实践管理路由
router.include_router(best_practices.router, tags=["projects-best-practices"])

# 高级分析路由
router.include_router(analysis.router, tags=["projects-analysis"])

# 项目成本和概览路由
router.include_router(costs.router, tags=["projects-costs"])
