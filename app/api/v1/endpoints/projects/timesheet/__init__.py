# -*- coding: utf-8 -*-
"""
项目工时管理模块（重构版本）

路由: /projects/{project_id}/timesheet/
- GET / - 获取项目工时记录列表（支持分页、搜索、排序、筛选）
- GET /summary - 获取项目工时汇总（自定义端点）
- GET /statistics - 获取项目工时统计（自定义端点）
- GET /{timesheet_id} - 获取工时记录详情
- POST / - 创建工时记录
- PUT /{timesheet_id} - 更新工时记录
- DELETE /{timesheet_id} - 删除工时记录
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .custom import router as custom_router

router = APIRouter()

# 注意：路由顺序很重要！
# 静态路径（如 /summary, /statistics）必须在动态路径（如 /{timesheet_id}）之前注册

# 先注册自定义端点（静态路径）
router.include_router(custom_router)

# 再注册CRUD路由（动态路径）
router.include_router(crud_router)
