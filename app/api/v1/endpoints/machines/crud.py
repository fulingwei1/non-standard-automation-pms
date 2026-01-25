# -*- coding: utf-8 -*-
"""
机台全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/machines/

迁移指南：
    GET  /machines/                    -> GET  /projects/{id}/machines/
    POST /machines/                    -> POST /projects/{id}/machines/
    GET  /machines/{id}                -> GET  /projects/{id}/machines/{id}
    PUT  /machines/{id}                -> PUT  /projects/{id}/machines/{id}
    DELETE /machines/{id}              -> DELETE /projects/{id}/machines/{id}
    PUT  /machines/{id}/progress       -> PUT  /projects/{id}/machines/{id}/progress
    GET  /machines/{id}/bom            -> GET  /projects/{id}/machines/{id}/bom
    GET  /machines/projects/{id}/summary     -> GET  /projects/{id}/machines/summary
    POST /machines/projects/{id}/recalculate -> POST /projects/{id}/machines/recalculate

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/machines/
