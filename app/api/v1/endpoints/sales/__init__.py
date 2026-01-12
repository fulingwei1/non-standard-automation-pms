# -*- coding: utf-8 -*-
"""
销售管理模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter
from . import leads, opportunities

# 导入旧的 sales.py 文件中的 router，包含统计等端点
from ..sales import router as legacy_sales_router

# 创建主路由
router = APIRouter()

# 聚合所有子路由（保持原有路由路径）
router.include_router(leads.router, tags=["sales-leads"])
router.include_router(opportunities.router, tags=["sales-opportunities"])

# 包含原有的销售 API 端点（统计、团队、目标等）
# 这些端点尚未拆分，暂时包含进来
for route in legacy_sales_router.routes:
    router.add_route(
        route.path,
        route.endpoint,
        methods=route.methods,
        name=route.name,
        include_in_schema=route.include_in_schema,
    )

# TODO: 继续添加其他模块路由
# router.include_router(quotes.router, tags=["sales-quotes"])
# router.include_router(contracts.router, tags=["sales-contracts"])
# router.include_router(invoices.router, tags=["sales-invoices"])
# router.include_router(payments.router, tags=["sales-payments"])
# ... 其他模块
