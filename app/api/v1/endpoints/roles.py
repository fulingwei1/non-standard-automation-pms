# -*- coding: utf-8 -*-
"""
角色管理 API endpoints

已拆分为模块化结构，详见 roles/ 目录：
- list_detail.py: 角色列表与详情（含权限列表）
- crud.py: 角色CRUD和权限分配
- nav_config.py: 导航菜单配置
"""

from .roles import router

__all__ = ["router"]
