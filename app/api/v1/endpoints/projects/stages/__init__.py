# -*- coding: utf-8 -*-
"""
项目阶段管理模块

路由: /projects/{project_id}/stages/
- POST /initialize - 初始化项目阶段
- DELETE /clear - 清除项目阶段
- GET / - 获取项目阶段列表
- GET /progress - 获取项目阶段进度概览
"""

from fastapi import APIRouter

from .crud import router as crud_router

router = APIRouter()

router.include_router(crud_router)
