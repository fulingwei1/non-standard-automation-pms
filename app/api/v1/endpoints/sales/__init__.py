# -*- coding: utf-8 -*-
"""
销售管理模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter
from . import leads, opportunities

# 创建主路由
router = APIRouter()

# 聚合所有子路由（保持原有路由路径）
router.include_router(leads.router, tags=["sales-leads"])
router.include_router(opportunities.router, tags=["sales-opportunities"])

# TODO: 继续添加其他模块路由
# router.include_router(quotes.router, tags=["sales-quotes"])
# router.include_router(contracts.router, tags=["sales-contracts"])
# router.include_router(invoices.router, tags=["sales-invoices"])
# router.include_router(payments.router, tags=["sales-payments"])
# ... 其他模块
