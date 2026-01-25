# -*- coding: utf-8 -*-
"""
工作日志全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，项目相关的工作日志功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/work-logs/

迁移指南：
    GET  /work-logs?project_id={id}     -> GET  /projects/{id}/work-logs/
    GET  /work-logs/project-summary/{id} -> GET /projects/{id}/work-logs/summary

用户个人工作日志创建和管理仍可使用 /api/v1/users/work-logs/ (如有需要)

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/work-logs/

__all__ = ["router"]
