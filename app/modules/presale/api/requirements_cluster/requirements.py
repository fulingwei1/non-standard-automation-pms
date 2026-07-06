# -*- coding: utf-8 -*-
"""
需求管理 API endpoints - 路由聚合

已拆分为模块化结构：
- requirement_details.py: 线索需求详情管理（get, create, update）
- requirement_freezes.py: 需求冻结管理（线索和商机的冻结记录）
- ai_clarifications.py: AI澄清管理（list, create for lead/opportunity, update, get）
"""

from fastapi import APIRouter

from . import (
    ai_clarifications,
    requirement_details,
    requirement_freezes,
)

router = APIRouter()

# 聚合所有子路由
router.include_router(requirement_details.router)
router.include_router(requirement_freezes.router)
router.include_router(ai_clarifications.router)
