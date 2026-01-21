# -*- coding: utf-8 -*-
"""
项目设备/机台管理模块

路由: /projects/{project_id}/machines/
- GET / - 获取项目机台列表
- POST / - 创建机台
- GET /{machine_id} - 获取机台详情
- PUT /{machine_id} - 更新机台
- PUT /{machine_id}/progress - 更新机台进度
- GET /{machine_id}/bom - 获取机台BOM
- DELETE /{machine_id} - 删除机台
- GET /summary - 项目机台汇总
- POST /recalculate - 重新计算项目聚合数据
"""

from fastapi import APIRouter

from .crud import router as crud_router

router = APIRouter()

router.include_router(crud_router, tags=["项目设备"])
