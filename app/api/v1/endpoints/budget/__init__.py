# -*- coding: utf-8 -*-
"""
项目预算管理模块

拆分自原 budget.py (646行)，按功能域分为：
- utils: 预算编号和版本号生成
- allocation_rules: 成本分摊规则CRUD
- budgets: 项目预算CRUD、提交、审批
- items: 预算明细CRUD

注意：路由顺序重要！allocation_rules 路由必须在 budgets 之前定义，
否则 /allocation-rules 会被 /{budget_id} 匹配。
"""

from fastapi import APIRouter

from .allocation_rules import router as allocation_rules_router
from .budgets import router as budgets_router
from .items import router as items_router

router = APIRouter()

# 成本分摊规则 - 必须在预算CRUD之前，避免 /allocation-rules 被 /{budget_id} 匹配
router.include_router(allocation_rules_router, tags=["成本分摊规则"])

# 项目预算CRUD
router.include_router(budgets_router, tags=["项目预算"])

# 预算明细
router.include_router(items_router, tags=["预算明细"])
