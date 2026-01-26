# -*- coding: utf-8 -*-
"""
项目成员管理模块

路由: /projects/{project_id}/members/
"""

from fastapi import APIRouter

from .crud import router as crud_router

router = APIRouter()

router.include_router(crud_router)
