# -*- coding: utf-8 -*-
"""
机台管理模块

⚠️ 注意：此模块的路由已迁移至项目子路由 /projects/{project_id}/machines/
独立的 /machines 路由已被删除，请使用项目中心API设计。

机台管理相关端点请使用：
- GET /projects/{project_id}/machines/ - 获取项目机台列表
- POST /projects/{project_id}/machines/ - 创建机台
- GET /projects/{project_id}/machines/{machine_id} - 获取机台详情
- PUT /projects/{project_id}/machines/{machine_id} - 更新机台
- DELETE /projects/{project_id}/machines/{machine_id} - 删除机台
- GET /projects/{project_id}/machines/summary - 获取项目机台汇总
- POST /projects/{project_id}/machines/recalculate - 重新计算项目聚合数据
- PUT /projects/{project_id}/machines/{machine_id}/progress - 更新机台进度
- GET /projects/{project_id}/machines/{machine_id}/bom - 获取机台BOM

服务历史和文档管理功能可能需要单独的路由或迁移至项目子路由。
"""

from fastapi import APIRouter

# 注意：由于独立的 /machines 路由已被删除，以下路由不会被注册
# 如需保留服务历史和文档管理功能，请考虑：
# 1. 迁移至项目子路由 /projects/{project_id}/machines/{machine_id}/service-history
# 2. 迁移至项目子路由 /projects/{project_id}/machines/{machine_id}/documents
# 3. 或创建新的独立路由（如果这些功能不依赖于项目上下文）

from .crud import router as crud_router
from .crud_refactored import router as crud_refactored_router
from .documents import router as documents_router
from .service_history import router as service_history_router

router = APIRouter()

# 机台CRUD已迁移至项目子路由，不再注册
# router.include_router(crud_refactored_router, tags=["机台管理"])

# 服务历史和文档管理功能需要迁移或创建新路由
# router.include_router(service_history_router, tags=["设备档案"])
# router.include_router(documents_router, tags=["机台文档"])
