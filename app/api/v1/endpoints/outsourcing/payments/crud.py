# -*- coding: utf-8 -*-
"""
外协付款 - CRUD操作
"""
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.outsourcing import OutsourcingOrder, OutsourcingPayment
from app.models.vendor import Vendor
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.outsourcing import (
    OutsourcingPaymentCreate,
    OutsourcingPaymentResponse,
)

from .utils import generate_payment_no
from app.common.query_filters import apply_pagination
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

router = APIRouter()


@router.get("/outsourcing-payments", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_outsourcing_payments(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    vendor_id: Optional[int] = Query(None, description="外协商ID筛选"),
    order_id: Optional[int] = Query(None, description="外协订单ID筛选"),
    payment_type: Optional[str] = Query(None, description="付款类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    start_date: Optional[date] = Query(None, description="开始日期筛选"),
    end_date: Optional[date] = Query(None, description="结束日期筛选"),
    current_user: User = Depends(security.require_permission("finance:read")),
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
    payments = apply_pagination(query.order_by(desc(OutsourcingPayment.payment_date)), pagination.offset, pagination.limit).all()

    items = []
    for payment in payments:
        vendor_name = None
        if payment.vendor_id:
            vendor = db.query(Vendor).filter(
                Vendor.id == payment.vendor_id,
                Vendor.vendor_type == 'OUTSOURCING'
            ).first()
            vendor_name = vendor.supplier_name if vendor else None

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

    return pagination.to_response(items, total)


@router.post("/outsourcing-payments", response_model=OutsourcingPaymentResponse, status_code=status.HTTP_201_CREATED)
def create_outsourcing_payment(
    *,
    db: Session = Depends(deps.get_db),
    payment_in: OutsourcingPaymentCreate,
    current_user: User = Depends(security.require_permission("finance:read")),
) -> Any:
    """
    创建外协付款记录
    """
    # 验证外协商是否存在
    vendor = db.query(Vendor).filter(
        Vendor.id == payment_in.vendor_id,
        Vendor.vendor_type == 'OUTSOURCING'
    ).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")

    # 验证外协订单（如果提供）
    if payment_in.order_id:
        order = get_or_404(db, OutsourcingOrder, payment_in.order_id, "外协订单不存在")
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
    vendor_name = vendor.supplier_name
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
