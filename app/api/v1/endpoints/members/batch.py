# -*- coding: utf-8 -*-
"""
项目成员批量操作全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/members/batch

迁移指南：
    POST /members/projects/{id}/members/batch -> POST /projects/{id}/members/batch

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/members/batch

__all__ = ["router"]
