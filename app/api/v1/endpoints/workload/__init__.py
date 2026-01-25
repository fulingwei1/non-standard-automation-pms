# -*- coding: utf-8 -*-
"""
资源排程与负荷管理全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，项目相关的负荷功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/workload/

迁移指南：
    GET  /workload/team?project_id={id}   -> GET  /projects/{id}/workload/team
    GET  /workload/gantt?project_id={id}  -> GET  /projects/{id}/workload/gantt
    GET  /workload/summary?project_id={id} -> GET /projects/{id}/workload/summary

用户个人负荷查询仍可使用 /api/v1/users/workload/ (如有需要)
技能管理相关功能请使用 /api/v1/skills/ (如有需要)

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/workload/

__all__ = ["router"]
