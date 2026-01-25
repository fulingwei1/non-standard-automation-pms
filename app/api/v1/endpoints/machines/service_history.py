# -*- coding: utf-8 -*-
"""
机台服务历史全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/machines/{machine_id}/service-history

迁移指南：
    GET /machines/{id}/service-history -> GET /projects/{pid}/machines/{id}/service-history

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/machines/{machine_id}/service-history

__all__ = ["router"]
