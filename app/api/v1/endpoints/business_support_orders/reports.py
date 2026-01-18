# -*- coding: utf-8 -*-
"""
商务支持模块 - 报表路由聚合

已拆分为模块化结构：
- sales_reports.py: 销售日报/周报/月报
- payment_reports.py: 回款统计报表
- contract_reports.py: 合同执行报表
- invoice_reports.py: 开票统计报表
"""

from fastapi import APIRouter

from . import contract_reports, invoice_reports, payment_reports, sales_reports

# 创建聚合路由
router = APIRouter()

# 聚合所有报表路由
router.include_router(sales_reports.router)
router.include_router(payment_reports.router)
router.include_router(contract_reports.router)
router.include_router(invoice_reports.router)
