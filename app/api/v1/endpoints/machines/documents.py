# -*- coding: utf-8 -*-
"""
机台文档管理全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/machines/{machine_id}/documents/

迁移指南：
    POST /machines/{id}/documents/upload     -> POST /projects/{pid}/machines/{id}/documents/upload
    GET  /machines/{id}/documents            -> GET  /projects/{pid}/machines/{id}/documents
    GET  /machines/{id}/documents/{did}/download -> GET /projects/{pid}/machines/{id}/documents/{did}/download
    GET  /machines/{id}/documents/{did}/versions -> GET /projects/{pid}/machines/{id}/documents/{did}/versions

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/machines/{machine_id}/documents/

__all__ = ["router"]
