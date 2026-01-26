# -*- coding: utf-8 -*-
"""
外协付款 - 工具函数
"""
from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.outsourcing import (
    OutsourcingDelivery,
    OutsourcingInspection,
    OutsourcingOrder,
    OutsourcingPayment,
)


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
