# -*- coding: utf-8 -*-
"""
角色管理模块

拆分自原 roles.py (739行)，按功能域分为：
- list_detail: 角色列表与详情（含权限列表）
- crud: 角色CRUD和权限分配
- nav_config: 导航菜单配置
- templates: 角色模板管理
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .list_detail import router as list_detail_router
from .nav_config import router as nav_config_router
from .templates import router as templates_router

router = APIRouter()

# 重要：特殊路径（不含路径参数的）必须放在动态路径（含{role_id}等）之前
# 角色CRUD和权限分配（包含特殊路径如inheritance-tree，必须在list_detail之前）
router.include_router(crud_router, tags=["角色管理"])

# 角色模板管理（特殊路径）
router.include_router(templates_router, prefix="/templates", tags=["角色模板"])

# 角色列表与详情（含路径参数{role_id}，必须放在最后）
router.include_router(list_detail_router, tags=["角色查询"])

# 导航菜单配置
router.include_router(nav_config_router, tags=["导航配置"])
