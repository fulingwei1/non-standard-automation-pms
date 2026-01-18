# -*- coding: utf-8 -*-
"""
到货跟踪 - 路由聚合

已拆分为模块化结构：
- arrival_crud.py: 基础CRUD操作（create, list, get, update_status, receive, delayed）
- arrival_follow_ups.py: 跟进记录管理（list, create）
- arrival_helpers.py: 辅助函数（编号生成、序列化）
"""

from fastapi import APIRouter

from . import arrival_crud, arrival_follow_ups

router = APIRouter()

# 聚合所有子路由
router.include_router(arrival_crud.router)
router.include_router(arrival_follow_ups.router)
