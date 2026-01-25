# -*- coding: utf-8 -*-
"""
工时管理全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/timesheet/

迁移指南：
    GET  /timesheet/timesheets          -> GET  /projects/{id}/timesheet/
    POST /timesheet/timesheets          -> POST /projects/{id}/timesheet/
    GET  /timesheet/timesheets/{id}     -> GET  /projects/{id}/timesheet/{id}
    GET  /timesheet/timesheets/week     -> GET  /projects/{id}/timesheet/week
    GET  /timesheet/timesheets/month    -> GET  /projects/{id}/timesheet/month
    GET  /timesheet/timesheets/statistics -> GET /projects/{id}/timesheet/statistics

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/timesheet/

__all__ = ["router"]
