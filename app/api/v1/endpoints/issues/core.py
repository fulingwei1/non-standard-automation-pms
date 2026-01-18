# -*- coding: utf-8 -*-
"""
问题管理核心端点 - 路由聚合

已拆分为模块化结构：
- crud.py: 基础CRUD操作（list, get, create, update）
- workflow.py: 工作流操作（assign, resolve, verify, change_status）
- follow_ups.py: 跟进记录操作
"""

from fastapi import APIRouter

from . import crud, follow_ups, workflow

router = APIRouter()

# 聚合所有子路由
router.include_router(crud.router)
router.include_router(workflow.router)
router.include_router(follow_ups.router)

# 导出辅助函数供其他模块使用
from .crud import _get_scoped_issue, build_issue_response

__all__ = ["router", "_get_scoped_issue", "build_issue_response"]
