# -*- coding: utf-8 -*-
"""
销售订单管理 - 工具函数
"""

from app.models.business_support import SalesOrder
from app.schemas.business_support import SalesOrderItemResponse, SalesOrderResponse


def build_sales_order_response(sales_order: SalesOrder) -> SalesOrderResponse:
    """构建销售订单响应对象"""
    items_data = [
        SalesOrderItemResponse(
            id=oi.id,
            sales_order_id=oi.sales_order_id,
            item_name=oi.item_name,
            item_spec=oi.item_spec,
            qty=oi.qty,
            unit=oi.unit,
            unit_price=oi.unit_price,
            amount=oi.amount,
            remark=oi.remark,
            created_at=oi.created_at,
            updated_at=oi.updated_at
        )
        for oi in sales_order.order_items
    ]

    return SalesOrderResponse(
        id=sales_order.id,
        order_no=sales_order.order_no,
        contract_id=sales_order.contract_id,
        contract_no=sales_order.contract_no,
        customer_id=sales_order.customer_id,
        customer_name=sales_order.customer_name,
        project_id=sales_order.project_id,
        project_no=sales_order.project_no,
        order_type=sales_order.order_type,
        order_amount=sales_order.order_amount,
        currency=sales_order.currency,
        required_date=sales_order.required_date,
        promised_date=sales_order.promised_date,
        order_status=sales_order.order_status,
        project_no_assigned=sales_order.project_no_assigned,
        project_no_assigned_date=sales_order.project_no_assigned_date,
        project_notice_sent=sales_order.project_notice_sent,
        project_notice_date=sales_order.project_notice_date,
        erp_order_no=sales_order.erp_order_no,
        erp_sync_status=sales_order.erp_sync_status,
        sales_person_id=sales_order.sales_person_id,
        sales_person_name=sales_order.sales_person_name,
        support_person_id=sales_order.support_person_id,
        remark=sales_order.remark,
        items=items_data,
        created_at=sales_order.created_at,
        updated_at=sales_order.updated_at
    )
