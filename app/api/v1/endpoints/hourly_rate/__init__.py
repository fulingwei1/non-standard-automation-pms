# -*- coding: utf-8 -*-
"""
时薪配置管理模块

拆分自原 hourly_rate.py (355行)，按功能域分为：
- crud: 时薪配置CRUD操作
- query: 时薪查询API（获取用户时薪、批量查询、历史记录）
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .query import router as query_router

router = APIRouter()

# 时薪查询API（先注册 /history 等静态路径，避免与 /{config_id} 冲突）
router.include_router(query_router, tags=["时薪查询"])

# 时薪配置CRUD
router.include_router(crud_router, tags=["时薪配置"])
