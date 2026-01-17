# -*- coding: utf-8 -*-
"""
文档管理模块

拆分自原 documents.py (325行)，按功能域分为：
- crud: 文档列表、详情、创建
- operations: 更新、下载、版本管理、删除
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .operations import router as operations_router

router = APIRouter()

# CRUD操作
router.include_router(crud_router, tags=["文档管理"])

# 文档操作（下载、版本、删除）
router.include_router(operations_router, tags=["文档操作"])
