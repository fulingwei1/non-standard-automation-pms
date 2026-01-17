# -*- coding: utf-8 -*-
"""
角色管理模块

拆分自原 roles.py (739行)，按功能域分为：
- list_detail: 角色列表与详情（含权限列表）
- crud: 角色CRUD和权限分配
- nav_config: 导航菜单配置
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .list_detail import router as list_detail_router
from .nav_config import router as nav_config_router

router = APIRouter()

# 角色列表与详情（含权限列表）
router.include_router(list_detail_router, tags=["角色查询"])

# 角色CRUD和权限分配
router.include_router(crud_router, tags=["角色管理"])

# 导航菜单配置
router.include_router(nav_config_router, tags=["导航配置"])
