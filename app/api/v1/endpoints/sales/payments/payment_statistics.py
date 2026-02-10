# -*- coding: utf-8 -*-
"""
回款统计分析 endpoints
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


@router.get("/payments/statistics", response_model=ResponseModel)
def get_payment_statistics(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    回款统计分析

    注意：此路由必须定义在 /payments/{payment_id} 之前，否则 FastAPI 会将 "statistics" 解析为 payment_id
    """
    from app.services.payment_statistics_service import (
        build_customer_list,
        build_invoice_query,
        build_monthly_list,
        calculate_customer_statistics,
        calculate_monthly_statistics,
        calculate_overdue_amount,
        calculate_status_statistics,
    )

    # 构建查询
    query = build_invoice_query(db, customer_id, start_date, end_date)
    invoices = query.all()

    today = date.today()

    # 计算各项统计
    monthly_stats = calculate_monthly_statistics(invoices)
    customer_stats = calculate_customer_statistics(invoices)
    status_stats = calculate_status_statistics(invoices)

    # 计算汇总
    total_invoiced = sum([invoice.total_amount or invoice.amount or Decimal("0") for invoice in invoices])
    total_paid = sum([invoice.paid_amount or Decimal("0") for invoice in invoices])
    total_unpaid = total_invoiced - total_paid
    total_overdue = calculate_overdue_amount(invoices, today)

    collection_rate = (total_paid / total_invoiced * 100) if total_invoiced > 0 else Decimal("0")

    # 构建列表
    monthly_list = build_monthly_list(monthly_stats)
    customer_list = build_customer_list(customer_stats, limit=10)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "summary": {
                "total_invoiced": float(total_invoiced),
                "total_paid": float(total_paid),
                "total_unpaid": float(total_unpaid),
                "total_overdue": float(total_overdue),
                "collection_rate": float(collection_rate),
                "invoice_count": len(invoices),
            },
            "monthly_statistics": monthly_list,
            "customer_statistics": customer_list,
            "status_statistics": {
                "PAID": {
                    "count": status_stats["PAID"]["count"],
                    "amount": float(status_stats["PAID"]["amount"])
                },
                "PARTIAL": {
                    "count": status_stats["PARTIAL"]["count"],
                    "amount": float(status_stats["PARTIAL"]["amount"])
                },
                "PENDING": {
                    "count": status_stats["PENDING"]["count"],
                    "amount": float(status_stats["PENDING"]["amount"])
                },
            }
        }
    )


@router.get("/payments/reminders", response_model=PaginatedResponse)
def get_payment_reminders(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    days_before: int = Query(7, ge=0, description="提前提醒天数"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取回款提醒列表（即将到期和已逾期的回款）

    注意：此路由必须定义在 /payments/{payment_id} 之前，否则 FastAPI 会将 "reminders" 解析为 payment_id
    """
    from app.models.sales import Invoice

    today = date.today()
    reminder_date = today + timedelta(days=days_before)

    query = db.query(Invoice).filter(
        Invoice.status == "ISSUED",
        Invoice.payment_status.in_(["PENDING", "PARTIAL"]),
        Invoice.due_date.isnot(None),
        Invoice.due_date <= reminder_date
    )

    total = query.count()
    invoices = query.order_by(Invoice.due_date).offset(pagination.offset).limit(pagination.limit).all()

    items = []
    for invoice in invoices:
        contract = invoice.contract
        unpaid = (invoice.total_amount or invoice.amount or Decimal("0")) - (invoice.paid_amount or Decimal("0"))
        days_until_due = (invoice.due_date - today).days if invoice.due_date else None
        is_overdue = days_until_due is not None and days_until_due < 0

        items.append({
            "id": invoice.id,
            "invoice_code": invoice.invoice_code,
            "contract_id": invoice.contract_id,
            "contract_code": contract.contract_code if contract else None,
            "project_id": invoice.project_id,
            "project_code": invoice.project.project_code if invoice.project else None,
            "customer_id": contract.customer_id if contract else None,
            "customer_name": contract.customer.customer_name if contract and contract.customer else None,
            "unpaid_amount": float(unpaid),
            "due_date": invoice.due_date,
            "days_until_due": days_until_due,
            "is_overdue": is_overdue,
            "overdue_days": abs(days_until_due) if is_overdue else None,
            "payment_status": invoice.payment_status,
            "reminder_level": "urgent" if is_overdue else ("warning" if days_until_due is not None and days_until_due <= 3 else "normal"),
        })

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )
