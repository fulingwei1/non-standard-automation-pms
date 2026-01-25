# -*- coding: utf-8 -*-
"""
项目成员扩展操作全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/members/

迁移指南：
    POST /members/projects/{id}/members/{mid}/notify-dept-manager -> POST /projects/{id}/members/{mid}/notify-dept-manager
    GET  /members/projects/{id}/members/from-dept/{did}           -> GET  /projects/{id}/members/from-dept/{did}

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/members/

__all__ = ["router"]
