# -*- coding: utf-8 -*-
"""
进度跟踪全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/progress/

迁移指南：
    GET  /progress/summary             -> GET  /projects/{id}/progress/summary
    GET  /progress/gantt               -> GET  /projects/{id}/progress/gantt
    GET  /progress/board               -> GET  /projects/{id}/progress/board
    GET  /progress/machines/{id}/summary -> GET /projects/{id}/progress/machines/{id}/summary

任务相关端点请使用全局任务API或项目中心进度API。

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/progress/

__all__ = ["router"]
