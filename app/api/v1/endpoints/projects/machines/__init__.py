# -*- coding: utf-8 -*-
"""
项目设备/机台管理模块（重构版本）

路由: /projects/{project_id}/machines/
- GET / - 获取项目机台列表（支持分页、搜索、排序、筛选）
- POST / - 创建机台（自动生成编码）
- GET /{machine_id} - 获取机台详情
- PUT /{machine_id} - 更新机台（阶段验证）
- DELETE /{machine_id} - 删除机台（BOM检查）
- GET /summary - 项目机台汇总（自定义端点）
- POST /recalculate - 重新计算项目聚合数据（自定义端点）
- PUT /{machine_id}/progress - 更新机台进度（自定义端点）
- GET /{machine_id}/bom - 获取机台BOM（自定义端点）
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .custom import router as custom_router

router = APIRouter()

# 注意：路由顺序很重要！
# 静态路径（如 /summary, /recalculate）必须在动态路径（如 /{machine_id}）之前注册

# 先注册自定义端点（静态路径）
router.include_router(custom_router)

# 再注册CRUD路由（动态路径）
router.include_router(crud_router)
