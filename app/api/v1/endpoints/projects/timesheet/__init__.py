# -*- coding: utf-8 -*-
"""
项目工时管理模块

路由: /projects/{project_id}/timesheet/
- GET / - 获取项目工时记录列表
- GET /summary - 获取项目工时汇总
- GET /statistics - 获取项目工时统计
"""

from fastapi import APIRouter

from .crud import router as crud_router

router = APIRouter()

router.include_router(crud_router)
