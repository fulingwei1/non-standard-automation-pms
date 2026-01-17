# -*- coding: utf-8 -*-
"""
里程碑管理模块

拆分自原 milestones.py (320行)，按功能域分为：
- crud: 里程碑列表、详情、创建、更新
- workflow: 完成里程碑（触发开票）、删除
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .workflow import router as workflow_router

router = APIRouter()

# CRUD操作
router.include_router(crud_router, tags=["里程碑管理"])

# 工作流操作（完成、删除）
router.include_router(workflow_router, tags=["里程碑工作流"])
