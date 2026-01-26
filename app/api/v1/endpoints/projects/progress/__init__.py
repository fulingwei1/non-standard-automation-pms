# -*- coding: utf-8 -*-
"""
项目进度管理模块

路由: /projects/{project_id}/progress/
- GET /summary - 项目进度汇总
- GET /gantt - 甘特图数据
- GET /board - 进度看板
- GET /machines/{machine_id}/summary - 机台进度汇总
"""

from fastapi import APIRouter

from .summary import router as summary_router

router = APIRouter()

router.include_router(summary_router)
