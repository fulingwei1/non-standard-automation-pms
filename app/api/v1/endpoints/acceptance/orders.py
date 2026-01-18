# -*- coding: utf-8 -*-
"""
验收单管理端点 - 路由聚合

已拆分为模块化结构：
- order_crud.py: 基础CRUD操作（list, get, create, update, delete）
- order_workflow.py: 工作流操作（submit, start, complete）
- order_items.py: 检查项管理（get items, update item result）
"""

from fastapi import APIRouter

from . import order_crud, order_items, order_workflow

router = APIRouter()

# 聚合所有子路由
router.include_router(order_crud.router)
router.include_router(order_workflow.router)
router.include_router(order_items.router)
