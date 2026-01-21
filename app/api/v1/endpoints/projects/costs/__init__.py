# -*- coding: utf-8 -*-
"""
项目成本管理模块

路由: /projects/{project_id}/costs/
- GET / - 获取项目成本列表
- POST / - 添加成本记录
- GET /{cost_id} - 获取成本详情
- PUT /{cost_id} - 更新成本
- DELETE /{cost_id} - 删除成本
- GET /summary - 成本汇总
"""

from fastapi import APIRouter

from .crud import router as crud_router

router = APIRouter()

router.include_router(crud_router)
