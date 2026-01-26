# -*- coding: utf-8 -*-
"""
项目工作量管理模块

路由: /projects/{project_id}/workload/
- GET /team - 获取项目团队负荷
- GET /gantt - 获取项目资源甘特图
- GET /summary - 获取项目工作量汇总
"""

from fastapi import APIRouter

from .crud import router as crud_router

router = APIRouter()

router.include_router(crud_router)
