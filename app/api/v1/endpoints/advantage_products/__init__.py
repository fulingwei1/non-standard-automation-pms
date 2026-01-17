# -*- coding: utf-8 -*-
"""
优势产品管理模块

拆分自原 advantage_products.py (591行)，按功能域分为：
- categories: 产品类别CRUD
- products: 优势产品CRUD
- import_excel: Excel批量导入
- match: 产品匹配检查
"""

from fastapi import APIRouter

from .categories import router as categories_router
from .import_excel import router as import_router
from .match import router as match_router
from .products import router as products_router

router = APIRouter()

# 产品类别管理
router.include_router(categories_router, tags=["产品类别"])

# 优势产品CRUD
router.include_router(products_router, tags=["优势产品"])

# Excel导入
router.include_router(import_router, tags=["产品导入"])

# 产品匹配
router.include_router(match_router, tags=["产品匹配"])
