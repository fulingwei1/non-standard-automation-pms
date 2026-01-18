# -*- coding: utf-8 -*-
"""
商机管理 API endpoints - 路由聚合

已拆分为模块化结构：
- opportunity_crud.py: 基础CRUD操作（list, create, get, update）
- opportunity_workflow.py: 工作流操作（gate, stage, score, win, lose）
- opportunity_analytics.py: 分析和导出（funnel, win-probability, export）
"""

from fastapi import APIRouter

from . import opportunity_analytics, opportunity_crud, opportunity_workflow

router = APIRouter()

# 聚合所有子路由
router.include_router(opportunity_crud.router)
router.include_router(opportunity_workflow.router)
router.include_router(opportunity_analytics.router)
