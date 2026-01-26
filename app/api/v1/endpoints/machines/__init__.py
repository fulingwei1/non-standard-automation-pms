# -*- coding: utf-8 -*-
"""
机台管理全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/machines/

迁移指南：
    CRUD操作        -> /projects/{id}/machines/
    文档管理        -> /projects/{id}/machines/{mid}/documents/
    服务历史        -> /projects/{id}/machines/{mid}/service-history

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 机台CRUD已迁移至项目子路由，不再注册
# 服务历史和文档管理功能需要迁移或创建新路由

__all__ = ["router"]
