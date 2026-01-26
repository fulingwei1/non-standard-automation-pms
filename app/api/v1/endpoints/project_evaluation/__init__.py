# -*- coding: utf-8 -*-
"""
项目评价全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/evaluations/

迁移指南：
    GET  /evaluations?project_id={id}    -> GET  /projects/{id}/evaluations/
    POST /evaluations                     -> POST /projects/{id}/evaluations/
    GET  /evaluations/{eval_id}           -> GET  /projects/{id}/evaluations/{eval_id}
    PUT  /evaluations/{eval_id}/confirm   -> PUT  /projects/{id}/evaluations/{eval_id}/confirm
    GET  /evaluations/statistics          -> GET  /projects/{id}/evaluations/statistics

评价维度配置请使用 /api/v1/evaluation-dimensions/ (如有需要)

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/evaluations/

__all__ = ["router"]
