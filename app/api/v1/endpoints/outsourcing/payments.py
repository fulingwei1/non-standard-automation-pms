# -*- coding: utf-8 -*-
"""
外协付款 - 自动生成
从 outsourcing.py 拆分
"""

# -*- coding: utf-8 -*-
"""
外协管理 API endpoints
包含：外协供应商、外协订单、交付与质检、进度与付款
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.outsourcing import (
    OutsourcingDelivery,
    OutsourcingDeliveryItem,
    OutsourcingEvaluation,
    OutsourcingInspection,
    OutsourcingOrder,
    OutsourcingOrderItem,
    OutsourcingPayment,
    OutsourcingProgress,
    OutsourcingVendor,
)
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.outsourcing import (
    OutsourcingDeliveryCreate,
    OutsourcingDeliveryResponse,
    OutsourcingInspectionCreate,
    OutsourcingInspectionResponse,
    OutsourcingOrderCreate,
    OutsourcingOrderItemCreate,
    OutsourcingOrderItemResponse,
    OutsourcingOrderListResponse,
    OutsourcingOrderResponse,
    OutsourcingOrderUpdate,
    OutsourcingPaymentCreate,
    OutsourcingPaymentResponse,
    OutsourcingPaymentUpdate,
    OutsourcingProgressCreate,
    OutsourcingProgressResponse,
    VendorCreate,
    VendorResponse,
    VendorUpdate,
)

router = APIRouter()


def generate_order_no(db: Session) -> str:
    """生成外协订单号：OS-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_order = (
        db.query(OutsourcingOrder)
        .filter(OutsourcingOrder.order_no.like(f"OS-{today}-%"))
        .order_by(desc(OutsourcingOrder.order_no))
        .first()
    )
    if max_order:
        seq = int(max_order.order_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"OS-{today}-{seq:03d}"


def generate_delivery_no(db: Session) -> str:
    """生成交付单号：DL-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_delivery = (
        db.query(OutsourcingDelivery)
        .filter(OutsourcingDelivery.delivery_no.like(f"DL-{today}-%"))
        .order_by(desc(OutsourcingDelivery.delivery_no))
        .first()
    )
    if max_delivery:
        seq = int(max_delivery.delivery_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"DL-{today}-{seq:03d}"


def generate_inspection_no(db: Session) -> str:
    """生成质检单号：IQ-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_inspection = (
        db.query(OutsourcingInspection)
        .filter(OutsourcingInspection.inspection_no.like(f"IQ-{today}-%"))
        .order_by(desc(OutsourcingInspection.inspection_no))
        .first()
    )
    if max_inspection:
        seq = int(max_inspection.inspection_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"IQ-{today}-{seq:03d}"


# NOTE: keep flat routes (no extra prefix) to preserve the original API paths.
# 共 4 个路由

# ==================== 外协付款 ====================

def generate_payment_no(db: Session) -> str:
    """生成付款单号：PY-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_payment = (
        db.query(OutsourcingPayment)
        .filter(OutsourcingPayment.payment_no.like(f"PY-{today}-%"))
        .order_by(desc(OutsourcingPayment.payment_no))
        .first()
    )
    if max_payment:
        seq = int(max_payment.payment_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"PY-{today}-{seq:03d}"


@router.get("/outsourcing-payments", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_outsourcing_payments(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    vendor_id: Optional[int] = Query(None, description="外协商ID筛选"),
    order_id: Optional[int] = Query(None, description="外协订单ID筛选"),
    payment_type: Optional[str] = Query(None, description="付款类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    start_date: Optional[date] = Query(None, description="开始日期筛选"),
    end_date: Optional[date] = Query(None, description="结束日期筛选"),
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    获取外协付款记录列表
    """
    query = db.query(OutsourcingPayment)

    if vendor_id:
        query = query.filter(OutsourcingPayment.vendor_id == vendor_id)

    if order_id:
        query = query.filter(OutsourcingPayment.order_id == order_id)

    if payment_type:
        query = query.filter(OutsourcingPayment.payment_type == payment_type)

    if status:
        query = query.filter(OutsourcingPayment.status == status)

    if start_date:
        query = query.filter(OutsourcingPayment.payment_date >= start_date)

    if end_date:
        query = query.filter(OutsourcingPayment.payment_date <= end_date)

    total = query.count()
    offset = (page - 1) * page_size
    payments = query.order_by(desc(OutsourcingPayment.payment_date)).offset(offset).limit(page_size).all()

    items = []
    for payment in payments:
        vendor_name = None
        if payment.vendor_id:
            vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == payment.vendor_id).first()
            vendor_name = vendor.vendor_name if vendor else None

        order_no = None
        if payment.order_id:
            order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == payment.order_id).first()
            order_no = order.order_no if order else None

        approved_by_name = None
        if payment.approved_by:
            approver = db.query(User).filter(User.id == payment.approved_by).first()
            approved_by_name = approver.real_name or approver.username if approver else None

        items.append(OutsourcingPaymentResponse(
            id=payment.id,
            payment_no=payment.payment_no,
            vendor_id=payment.vendor_id,
            vendor_name=vendor_name,
            order_id=payment.order_id,
            order_no=order_no,
            payment_type=payment.payment_type,
            payment_amount=payment.payment_amount,
            payment_date=payment.payment_date,
            payment_method=payment.payment_method,
            invoice_no=payment.invoice_no,
            invoice_amount=payment.invoice_amount,
            invoice_date=payment.invoice_date,
            status=payment.status,
            approved_by=payment.approved_by,
            approved_by_name=approved_by_name,
            approved_at=payment.approved_at,
            remark=payment.remark,
            created_at=payment.created_at,
            updated_at=payment.updated_at
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/outsourcing-payments", response_model=OutsourcingPaymentResponse, status_code=status.HTTP_201_CREATED)
def create_outsourcing_payment(
    *,
    db: Session = Depends(deps.get_db),
    payment_in: OutsourcingPaymentCreate,
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    创建外协付款记录
    """
    # 验证外协商是否存在
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == payment_in.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")

    # 验证外协订单（如果提供）
    if payment_in.order_id:
        order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == payment_in.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="外协订单不存在")
        if order.vendor_id != payment_in.vendor_id:
            raise HTTPException(status_code=400, detail="外协订单不属于该外协商")

    payment_no = generate_payment_no(db)

    payment = OutsourcingPayment(
        payment_no=payment_no,
        vendor_id=payment_in.vendor_id,
        order_id=payment_in.order_id,
        payment_type=payment_in.payment_type,
        payment_amount=payment_in.payment_amount,
        payment_date=payment_in.payment_date,
        payment_method=payment_in.payment_method,
        invoice_no=payment_in.invoice_no,
        invoice_amount=payment_in.invoice_amount,
        invoice_date=payment_in.invoice_date,
        status="DRAFT",
        created_by=current_user.id
    )

    db.add(payment)

    # 如果关联了订单，更新订单的已付金额和付款状态
    if payment_in.order_id:
        order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == payment_in.order_id).first()
        if order:
            order.paid_amount = (order.paid_amount or Decimal("0")) + payment_in.payment_amount
            # 判断付款状态
            if order.paid_amount >= order.amount_with_tax:
                order.payment_status = "PAID"
            elif order.paid_amount > Decimal("0"):
                order.payment_status = "PARTIAL"
            else:
                order.payment_status = "UNPAID"

    db.commit()
    db.refresh(payment)

    # 构建响应
    vendor_name = vendor.vendor_name
    order_no = None
    if payment.order_id:
        order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == payment.order_id).first()
        order_no = order.order_no if order else None

    return OutsourcingPaymentResponse(
        id=payment.id,
        payment_no=payment.payment_no,
        vendor_id=payment.vendor_id,
        vendor_name=vendor_name,
        order_id=payment.order_id,
        order_no=order_no,
        payment_type=payment.payment_type,
        payment_amount=payment.payment_amount,
        payment_date=payment.payment_date,
        payment_method=payment.payment_method,
        invoice_no=payment.invoice_no,
        invoice_amount=payment.invoice_amount,
        invoice_date=payment.invoice_date,
        status=payment.status,
        approved_by=payment.approved_by,
        approved_by_name=None,
        approved_at=payment.approved_at,
        remark=payment.remark,
        created_at=payment.created_at,
        updated_at=payment.updated_at
    )


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

