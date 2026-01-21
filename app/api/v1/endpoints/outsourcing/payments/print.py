# -*- coding: utf-8 -*-
"""
外协付款 - 打印功能
"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.outsourcing import (
    OutsourcingDelivery,
    OutsourcingOrder,
    OutsourcingOrderItem,
    OutsourcingPayment,
)
from app.models.project import Machine, Project
from app.models.user import User

router = APIRouter()


@router.get("/outsourcing-orders/{order_id}/print", response_model=dict, status_code=status.HTTP_200_OK)
def print_outsourcing_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    外协订单打印
    返回订单的打印数据（包含订单信息、明细、供应商信息等）
    """
    from app.models.outsourcing import OutsourcingVendor

    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")

    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == order.vendor_id).first()
    project = db.query(Project).filter(Project.id == order.project_id).first()
    machine = None
    if order.machine_id:
        machine = db.query(Machine).filter(Machine.id == order.machine_id).first()

    # 获取订单明细
    order_items = db.query(OutsourcingOrderItem).filter(
        OutsourcingOrderItem.order_id == order_id
    ).order_by(OutsourcingOrderItem.item_no).all()

    items_data = []
    for item in order_items:
        items_data.append({
            "item_no": item.item_no,
            "material_code": item.material_code,
            "material_name": item.material_name,
            "specification": item.specification,
            "drawing_no": item.drawing_no,
            "process_type": item.process_type,
            "unit": item.unit,
            "quantity": float(item.quantity),
            "unit_price": float(item.unit_price),
            "amount": float(item.amount),
            "material_provided": item.material_provided,
        })

    # 获取交付记录
    deliveries = db.query(OutsourcingDelivery).filter(
        OutsourcingDelivery.order_id == order_id
    ).order_by(OutsourcingDelivery.delivery_date).all()

    deliveries_data = []
    for delivery in deliveries:
        deliveries_data.append({
            "delivery_no": delivery.delivery_no,
            "delivery_date": delivery.delivery_date.isoformat() if delivery.delivery_date else None,
            "delivery_qty": float(delivery.delivery_qty or 0),
            "status": delivery.status,
        })

    # 获取付款记录
    payments = db.query(OutsourcingPayment).filter(
        OutsourcingPayment.order_id == order_id
    ).order_by(OutsourcingPayment.payment_date).all()

    payments_data = []
    for payment in payments:
        payments_data.append({
            "payment_type": payment.payment_type,
            "payment_amount": float(payment.payment_amount or 0),
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
            "payment_method": payment.payment_method,
            "status": payment.status,
        })

    return {
        "order": {
            "order_no": order.order_no,
            "order_title": order.order_title,
            "order_type": order.order_type,
            "total_amount": float(order.total_amount or 0),
            "tax_rate": float(order.tax_rate or 0),
            "tax_amount": float(order.tax_amount or 0),
            "amount_with_tax": float(order.amount_with_tax or 0),
            "required_date": order.required_date.isoformat() if order.required_date else None,
            "estimated_date": order.estimated_date.isoformat() if order.estimated_date else None,
            "actual_date": order.actual_date.isoformat() if order.actual_date else None,
            "status": order.status,
            "payment_status": order.payment_status,
            "paid_amount": float(order.paid_amount or 0),
            "created_at": order.created_at.isoformat() if order.created_at else None,
        },
        "vendor": {
            "vendor_name": vendor.vendor_name if vendor else None,
            "contact_person": vendor.contact_person if vendor else None,
            "contact_phone": vendor.contact_phone if vendor else None,
            "address": vendor.address if vendor else None,
        } if vendor else None,
        "project": {
            "project_name": project.project_name if project else None,
            "project_code": project.project_code if project else None,
        } if project else None,
        "machine": {
            "machine_name": machine.machine_name if machine else None,
            "machine_code": machine.machine_code if machine else None,
        } if machine else None,
        "items": items_data,
        "deliveries": deliveries_data,
        "payments": payments_data,
        "print_time": datetime.now().isoformat(),
    }
