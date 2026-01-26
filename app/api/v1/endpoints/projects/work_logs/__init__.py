# -*- coding: utf-8 -*-
"""
项目工作日志模块

路由: /projects/{project_id}/work-logs/
提供项目相关工作日志的只读视图
"""

from fastapi import APIRouter

from .crud import router as crud_router

router = APIRouter()

router.include_router(crud_router)
