# -*- coding: utf-8 -*-
"""
商务支持订单模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter
from . import (
    sales_orders,
    delivery_orders,
    acceptance_tracking,
    reconciliations,
    invoice_requests,
    customer_registrations,
    reports
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
router.include_router(reports.router, tags=["business-support-reports"])
