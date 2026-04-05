# -*- coding: utf-8 -*-
"""
采购管理优化模块

包含：
- suppliers: 供应商管理 API
- price_analysis: 采购价格分析
- kitting_analysis: 采购齐套率分析
"""

from fastapi import APIRouter

from .kitting_analysis import router as kitting_router
from .price_analysis import router as price_router
from .suppliers import router as suppliers_router

router = APIRouter()

# 供应商管理 /api/v1/procurement/suppliers/*
router.include_router(suppliers_router, prefix="/suppliers", tags=["供应商管理"])

# 价格分析 /api/v1/procurement/price-analysis
router.include_router(price_router, prefix="/price-analysis", tags=["采购价格分析"])

# 齐套率分析 /api/v1/procurement/kitting-analysis
router.include_router(kitting_router, prefix="/kitting-analysis", tags=["采购齐套率分析"])
