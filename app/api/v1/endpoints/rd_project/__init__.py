# -*- coding: utf-8 -*-
"""
研发项目 API - 模块化结构

拆分为以下模块：
- utils.py: 工具函数（编号生成）
- categories.py: 研发项目分类管理
- initiation.py: 研发项目立项（CRUD、审批、结项）
- expense_types.py: 研发费用类型管理
- expenses.py: 研发费用归集（录入、查询、汇总、计算）
- allocation.py: 费用分摊规则（分摊规则、工时汇总）
- worklogs.py: 研发项目工作日志
- documents.py: 研发项目文档管理
"""

from fastapi import APIRouter

from .allocation import router as allocation_router
from .categories import router as categories_router
from .documents import router as documents_router
from .expense_types import router as expense_types_router
from .expenses import router as expenses_router
from .initiation import router as initiation_router
from .worklogs import router as worklogs_router

# 创建主路由
router = APIRouter()

# 聚合子路由
# 静态路径必须在initiation（含/{project_id}动态路径）之前
router.include_router(categories_router)
router.include_router(expense_types_router)
router.include_router(expenses_router)
router.include_router(allocation_router)
router.include_router(initiation_router)
router.include_router(worklogs_router)
router.include_router(documents_router)

__all__ = ['router']
