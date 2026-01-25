# -*- coding: utf-8 -*-
"""
文档管理模块

拆分自原 documents.py (325行)，按功能域分为：
- crud: 文档列表、详情、创建
- operations: 更新、下载、版本管理、删除
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .crud_refactored import router as crud_refactored_router
from .operations import router as operations_router

router = APIRouter()

# CRUD操作（使用重构版本，统一响应格式）
router.include_router(crud_refactored_router, tags=["文档管理"])
# 原版本保留作为参考
# router.include_router(crud_router, tags=["文档管理"])

# 文档操作（下载、版本、删除）
router.include_router(operations_router, tags=["文档操作"])
