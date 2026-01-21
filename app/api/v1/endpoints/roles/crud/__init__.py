# -*- coding: utf-8 -*-
"""
角色CRUD和权限分配端点模块

模块结构:
 ├── utils.py         # 工具函数
 ├── role_crud.py     # 角色CRUD操作
 ├── permissions.py   # 权限分配
 ├── role_detail.py   # 角色详情和比较
 └── inheritance.py   # 继承树
"""

from fastapi import APIRouter

from . import inheritance, permissions, role_crud, role_detail, utils

# 创建主路由
router = APIRouter()

# 聚合所有子路由
router.include_router(role_crud.router, tags=["角色管理"])
router.include_router(permissions.router, tags=["角色管理"])
router.include_router(role_detail.router, tags=["角色管理"])
router.include_router(inheritance.router, tags=["角色管理"])

__all__ = ["router"]
