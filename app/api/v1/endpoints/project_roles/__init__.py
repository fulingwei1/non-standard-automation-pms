# -*- coding: utf-8 -*-
"""
项目角色全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/roles/

迁移指南：
    GET  /project-roles/projects/{id}/overview -> GET  /projects/{id}/roles/overview
    GET  /project-roles/projects/{id}/configs  -> GET  /projects/{id}/roles/configs
    GET  /project-roles/projects/{id}/leads    -> GET  /projects/{id}/roles/leads
    POST /project-roles/projects/{id}/leads    -> POST /projects/{id}/roles/leads
    GET  /project-roles/projects/{id}/team     -> GET  /projects/{id}/roles/team

角色类型字典请使用 /api/v1/role-types/ (如有需要)

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/roles/

__all__ = ["router"]
