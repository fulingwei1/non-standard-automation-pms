# -*- coding: utf-8 -*-
"""
阶段管理全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/stages/

迁移指南：
    GET  /stages?project_id={id}           -> GET  /projects/{id}/stages/
    GET  /stages/projects/{id}/stages      -> GET  /projects/{id}/stages/
    POST /stages                           -> POST /projects/{id}/stages/
    GET  /stages/{stage_id}                -> GET  /projects/{id}/stages/{stage_id}
    PUT  /stages/{stage_id}                -> PUT  /projects/{id}/stages/{stage_id}
    PUT  /stages/project-stages/{id}       -> PUT  /projects/{id}/stages/{id}/progress
    GET  /stages/statuses                  -> GET  /projects/{id}/stages/statuses
    GET  /stages/project-stages/{id}/statuses -> GET /projects/{id}/stages/{id}/statuses

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/stages/

__all__ = ["router"]
