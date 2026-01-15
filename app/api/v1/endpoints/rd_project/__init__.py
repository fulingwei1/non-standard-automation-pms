# -*- coding: utf-8 -*-
"""
研发项目 API - 模块化结构
"""

from fastapi import APIRouter

from .categories import router as categories_router
from .initiation import router as initiation_router
from .expense_types import router as expense_types_router
from .expenses import router as expenses_router
from .allocation import router as allocation_router
from .worklogs import router as worklogs_router
from .documents import router as documents_router

router = APIRouter()

router.include_router(categories_router)
router.include_router(initiation_router)
router.include_router(expense_types_router)
router.include_router(expenses_router)
router.include_router(allocation_router)
router.include_router(worklogs_router)
router.include_router(documents_router)

__all__ = ['router']
