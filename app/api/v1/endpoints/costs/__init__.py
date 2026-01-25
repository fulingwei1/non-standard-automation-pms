# -*- coding: utf-8 -*-
"""
成本管理全局端点 - 兼容层

⚠️ 已废弃 (DEPRECATED)
此模块已废弃，所有功能已迁移到项目中心端点。

请使用：
    /api/v1/projects/{project_id}/costs/

迁移指南：
    基础CRUD      -> /projects/{id}/costs/
    成本汇总      -> /projects/{id}/costs/summary
    成本分析      -> /projects/{id}/costs/analysis
    人工成本      -> /projects/{id}/costs/labor
    成本分摊      -> /projects/{id}/costs/allocation
    预算分析      -> /projects/{id}/costs/budget

此模块将在未来版本中移除。
"""

from fastapi import APIRouter

router = APIRouter()

# 此路由已完全废弃，不再提供任何端点
# 请使用 /api/v1/projects/{project_id}/costs/

__all__ = ["router"]
