# -*- coding: utf-8 -*-
"""
项目角色管理模块

路由: /projects/{project_id}/roles/
- GET /leads - 获取项目负责人列表
- POST /leads - 指定项目负责人
- PUT /leads/{member_id} - 更新项目负责人
- DELETE /leads/{member_id} - 移除项目负责人
- GET /leads/{member_id}/team - 获取团队成员
- POST /leads/{member_id}/team - 添加团队成员
- DELETE /leads/{lead_id}/team/{member_id} - 移除团队成员
- GET /configs - 获取项目角色配置
- POST /configs/init - 初始化项目角色配置
- PUT /configs - 批量更新项目角色配置
- GET /overview - 获取项目角色概览
"""

from fastapi import APIRouter

from .configs import router as configs_router
from .leads import router as leads_router
from .overview import router as overview_router
from .team_members import router as team_router

router = APIRouter()

# 负责人路由
router.include_router(leads_router, tags=["projects-roles-leads"])

# 团队成员路由
router.include_router(team_router, tags=["projects-roles-team"])

# 角色配置路由
router.include_router(configs_router, tags=["projects-roles-configs"])

# 角色概览路由
router.include_router(overview_router, tags=["projects-roles-overview"])
