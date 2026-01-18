# -*- coding: utf-8 -*-
"""
物料替代 API endpoints - 路由聚合

已拆分为模块化结构：
- substitution_crud.py: 基础CRUD操作（list, get, create）
- substitution_workflow.py: 审批流程（tech-approve, prod-approve, execute）
"""

from fastapi import APIRouter

from . import substitution_crud, substitution_workflow

router = APIRouter()

# 聚合所有子路由
router.include_router(substitution_crud.router)
router.include_router(substitution_workflow.router)
