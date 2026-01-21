# -*- coding: utf-8 -*-
"""
外协付款 - 对账单
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.outsourcing import (
    OutsourcingDelivery,
    OutsourcingOrder,
    OutsourcingOrderItem,
    OutsourcingPayment,
    OutsourcingVendor,
)
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/outsourcing-vendors/{vendor_id}/statement", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_vendor_statement(
    vendor_id: int,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    外协对账单
    生成指定供应商的对账单，包含订单、交付、付款等明细
    """
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协供应商不存在")

    # 获取订单列表
    orders_query = db.query(OutsourcingOrder).filter(OutsourcingOrder.vendor_id == vendor_id)
    if start_date:
        orders_query = orders_query.filter(OutsourcingOrder.order_date >= start_date)
    if end_date:
        orders_query = orders_query.filter(OutsourcingOrder.order_date <= end_date)
    orders = orders_query.order_by(OutsourcingOrder.order_date).all()

    # 构建对账单明细
    statement_items = []
    total_order_amount = Decimal("0")
    total_paid_amount = Decimal("0")
    total_pending_amount = Decimal("0")

    for order in orders:
        # 获取订单明细
        order_items = db.query(OutsourcingOrderItem).filter(
            OutsourcingOrderItem.order_id == order.id
        ).all()

        order_total = sum(float(item.unit_price or 0) * float(item.quantity or 0) for item in order_items)
        total_order_amount += Decimal(str(order_total))

        # 获取付款记录
        payments = db.query(OutsourcingPayment).filter(
            OutsourcingPayment.order_id == order.id,
            OutsourcingPayment.status == 'PAID'
        ).all()

        paid_amount = sum(float(payment.payment_amount or 0) for payment in payments)
        total_paid_amount += Decimal(str(paid_amount))

        pending_amount = order_total - paid_amount
        total_pending_amount += Decimal(str(pending_amount))

        # 获取交付记录
        deliveries = db.query(OutsourcingDelivery).filter(
            OutsourcingDelivery.order_id == order.id
        ).all()

        statement_items.append({
            "order_id": order.id,
            "order_no": order.order_no,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "order_amount": round(order_total, 2),
            "paid_amount": round(paid_amount, 2),
            "pending_amount": round(pending_amount, 2),
            "order_status": order.status,
            "deliveries": [
                {
                    "delivery_no": d.delivery_no,
                    "delivery_date": d.delivery_date.isoformat() if d.delivery_date else None,
                    "delivery_qty": float(d.total_qty or 0)
                }
                for d in deliveries
            ],
            "payments": [
                {
                    "payment_no": p.payment_no,
                    "payment_date": p.payment_date.isoformat() if p.payment_date else None,
                    "payment_amount": float(p.payment_amount or 0),
                    "payment_type": p.payment_type
                }
                for p in payments
            ]
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "vendor_id": vendor_id,
            "vendor_name": vendor.vendor_name,
            "vendor_code": vendor.vendor_code,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "summary": {
                "total_orders": len(orders),
                "total_order_amount": float(total_order_amount),
                "total_paid_amount": float(total_paid_amount),
                "total_pending_amount": float(total_pending_amount)
            },
            "items": statement_items,
            "generated_at": datetime.now().isoformat()
        }
    )
