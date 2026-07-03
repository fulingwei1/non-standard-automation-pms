# -*- coding: utf-8 -*-
"""
线索管理 API endpoints 聚合模块
"""

from fastapi import APIRouter

from . import actions, crud, follow_ups

# 创建主路由
router = APIRouter()

# 聚合所有子模块的路由
# 静态入口（例如 /leads/export）必须先于 /leads/{lead_id} 注册。
router.include_router(actions.router)
router.include_router(follow_ups.router)
router.include_router(crud.router)
