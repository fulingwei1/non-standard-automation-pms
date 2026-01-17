# -*- coding: utf-8 -*-
"""
机台管理模块

拆分自原 machines.py (693行)，按功能域分为：
- crud: 机台CRUD、BOM查询
- service_history: 服务历史记录
- documents: 文档上传、下载、版本管理
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .documents import router as documents_router
from .service_history import router as service_history_router

router = APIRouter()

# 机台CRUD
router.include_router(crud_router, tags=["机台管理"])

# 服务历史
router.include_router(service_history_router, tags=["设备档案"])

# 文档管理
router.include_router(documents_router, tags=["机台文档"])
