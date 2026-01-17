# -*- coding: utf-8 -*-
"""
技术规格管理模块

拆分自原 technical_spec.py (456行)，按功能域分为：
- requirements: 技术规格要求CRUD
- match: 规格匹配检查
- extract: 规格提取
"""

from fastapi import APIRouter

from .extract import router as extract_router
from .match import router as match_router
from .requirements import router as requirements_router

router = APIRouter()

# 规格提取（/requirements/extract 需放在 /requirements/{id} 之前）
router.include_router(extract_router, tags=["规格提取"])

# 技术规格要求CRUD
router.include_router(requirements_router, tags=["规格要求"])

# 规格匹配检查
router.include_router(match_router, tags=["规格匹配"])
