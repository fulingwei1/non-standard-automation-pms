# -*- coding: utf-8 -*-
"""
项目角色类型与负责人管理模块

拆分自原 project_roles.py (779行)，按功能域分为：
- role_types: 角色类型字典管理（系统管理员）
- role_configs: 项目角色配置管理（项目管理员）
- leads: 项目负责人管理（项目经理）
- team_members: 团队成员管理（负责人）
- overview: 项目角色概览
"""

from fastapi import APIRouter

from .leads import router as leads_router
from .overview import router as overview_router
from .role_configs import router as configs_router
from .role_types import router as types_router
from .team_members import router as team_router

router = APIRouter()

# 角色类型字典
router.include_router(types_router, tags=["角色类型"])

# 项目角色配置
router.include_router(configs_router, tags=["角色配置"])

# 项目负责人
router.include_router(leads_router, tags=["项目负责人"])

# 团队成员
router.include_router(team_router, tags=["团队成员"])

# 角色概览
router.include_router(overview_router, tags=["角色概览"])
