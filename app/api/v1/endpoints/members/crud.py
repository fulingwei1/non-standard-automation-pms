# -*- coding: utf-8 -*-
"""
项目成员全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/members/

迁移指南：
    GET  /members/              -> GET  /projects/{id}/members/
    POST /members/              -> POST /projects/{id}/members/
    PUT  /members/{id}          -> PUT  /projects/{id}/members/{id}
    DELETE /members/{id}        -> DELETE /projects/{id}/members/{id}

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/members/
