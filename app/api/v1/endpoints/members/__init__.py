# -*- coding: utf-8 -*-
"""
项目成员模块

拆分自原 members.py (507行)，按功能域分为：
- crud: 成员 CRUD 操作
- conflicts: 冲突检查
- batch: 批量操作
- extended: 扩展操作（通知、部门用户列表）
"""

from fastapi import APIRouter

from .batch import router as batch_router
from .conflicts import router as conflicts_router
from .crud import router as crud_router
from .extended import router as extended_router

router = APIRouter()

# 成员 CRUD 操作
router.include_router(crud_router, tags=["项目成员"])

# 冲突检查
router.include_router(conflicts_router, tags=["成员冲突"])

# 批量操作
router.include_router(batch_router, tags=["成员批量"])

# 扩展操作
router.include_router(extended_router, tags=["成员扩展"])
