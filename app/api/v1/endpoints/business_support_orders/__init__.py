# -*- coding: utf-8 -*-
"""
商务支持订单模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter

from . import (
    acceptance_tracking,
    contract_reports,
    customer_registrations,
    delivery_orders,
    invoice_reports,
    invoice_requests,
    payment_reports,
    reconciliations,
    sales_reports,
    sales_orders,
)

# 创建主路由
router = APIRouter()

# 聚合所有子路由（保持原有路由路径）
router.include_router(sales_orders.router, tags=["business-support-orders"])
router.include_router(delivery_orders.router, tags=["business-support-delivery"])
router.include_router(acceptance_tracking.router, tags=["business-support-acceptance"])
router.include_router(reconciliations.router, tags=["business-support-reconciliations"])
router.include_router(invoice_requests.router, tags=["business-support-invoices"])
router.include_router(customer_registrations.router, tags=["business-support-registrations"])
# 报表路由（已拆分为多个模块）
router.include_router(sales_reports.router, tags=["business-support-reports"])
router.include_router(payment_reports.router, tags=["business-support-reports"])
router.include_router(contract_reports.router, tags=["business-support-reports"])
router.include_router(invoice_reports.router, tags=["business-support-reports"])
