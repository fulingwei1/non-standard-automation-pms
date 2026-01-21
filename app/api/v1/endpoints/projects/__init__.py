# -*- coding: utf-8 -*-
"""
项目管理模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中

模块结构:
 ├── core.py           # 核心CRUD
 ├── status.py         # 状态管理
 ├── payment_plans.py  # 付款计划
 ├── templates.py      # 项目模板
 ├── cache.py          # 缓存管理
 ├── archive.py        # 归档管理
 ├── overview.py       # 概览/仪表盘 (新)
 ├── sync.py           # 数据同步/ERP (新)
 ├── extended.py       # 扩展功能（复盘、分析等）
 ├── gate_checks.py    # 阶段门校验
 ├── milestones/       # 项目里程碑（新迁移）
 └── utils.py          # 工具函数
"""

from fastapi import APIRouter

from . import (
    archive,
    cache,
    core,
    extended,
    ext_best_practices,
    overview,
    payment_plans,
    status,
    sync,
    templates,
)

# Export gate check functions for use by stage_advance_service
from .gate_checks import check_gate, check_gate_detailed

__all__ = [
    "check_gate",
    "check_gate_detailed",
    "router",
]

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

# 概览和仪表盘路由
router.include_router(overview.router, tags=["projects-overview"])

# 数据同步路由（合同同步、ERP集成）
router.include_router(sync.router, tags=["projects-sync"])

# 最佳实践路由（放在 core 之前，避免与/{project_id}冲突）
router.include_router(ext_best_practices.router, tags=["projects-best-practices"])

# 核心CRUD路由
router.include_router(core.router, tags=["projects-core"])

# 状态管理路由
router.include_router(status.router, tags=["projects-status"])

# 付款计划路由
router.include_router(payment_plans.router, tags=["projects-payment-plans"])

# 扩展功能路由（复盘、经验教训、高级分析等）
router.include_router(extended.router, tags=["projects-extended"])

# === 项目模块整合：迁移的子模块路由 ===
from .machines import router as machines_router
from .members import router as members_router
from .milestones import router as milestones_router
from .resource_plan import router as resource_plan_router

# 里程碑路由（项目内操作）
router.include_router(
    milestones_router,
    prefix="/{project_id}/milestones",
    tags=["projects-milestones"],
)

# 机台路由（项目内操作）
router.include_router(
    machines_router,
    prefix="/{project_id}/machines",
    tags=["projects-machines"],
)

# 资源计划路由（项目内操作）
router.include_router(
    resource_plan_router,
    prefix="/{project_id}/resource-plan",
    tags=["projects-resource-plan"],
)

# 成员路由（项目内操作）
router.include_router(
    members_router,
    prefix="/{project_id}/members",
    tags=["projects-members"],
)
