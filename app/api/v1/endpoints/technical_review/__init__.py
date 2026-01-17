# -*- coding: utf-8 -*-
"""
技术评审管理模块

拆分自原 technical_review.py (872行)，按功能域分为：
- utils: 辅助工具函数
- reviews: 评审主表 CRUD
- participants: 参与人管理
- materials: 材料管理
- checklists: 检查项记录
- issues: 问题管理
"""

from fastapi import APIRouter

from .checklists import router as checklists_router
from .issues import router as issues_router
from .materials import router as materials_router
from .participants import router as participants_router
from .reviews import router as reviews_router

router = APIRouter()

# 评审主表
router.include_router(reviews_router, tags=["技术评审"])

# 参与人
router.include_router(participants_router, tags=["评审参与人"])

# 材料
router.include_router(materials_router, tags=["评审材料"])

# 检查项
router.include_router(checklists_router, tags=["评审检查项"])

# 问题
router.include_router(issues_router, tags=["评审问题"])
