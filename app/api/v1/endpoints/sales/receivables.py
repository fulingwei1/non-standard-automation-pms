# -*- coding: utf-8 -*-
"""
应收账款管理 API endpoints

包含：
- 应收账龄分析
- 逾期应收列表
- 应收账款汇总统计
"""

from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.sales import Contract, Invoice
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


# ==================== 应收账款分析 ====================


@router.get("/receivables/aging", response_model=ResponseModel)
def get_receivables_aging(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    应收账龄分析（已集成数据权限过滤）
    """
    from app.core.sales_permissions import filter_sales_finance_data_by_scope

    query = db.query(Invoice).filter(
        Invoice.status == "ISSUED",
        Invoice.payment_status.in_(["PENDING", "PARTIAL"])
    )

    # 应用数据权限过滤（发票使用财务数据权限）
    query = filter_sales_finance_data_by_scope(query, current_user, db, Invoice, "created_by")

    if customer_id:
        query = query.join(Contract).filter(Contract.customer_id == customer_id)

    if contract_id:
        query = query.filter(Invoice.contract_id == contract_id)

    invoices = query.all()

    today = date.today()
    aging_buckets = {
        "0-30": {"count": 0, "amount": Decimal("0")},
        "31-60": {"count": 0, "amount": Decimal("0")},
        "61-90": {"count": 0, "amount": Decimal("0")},
        "90+": {"count": 0, "amount": Decimal("0")},
    }

    total_unpaid = Decimal("0")

    for invoice in invoices:
        if not invoice.due_date:
            continue

        unpaid = (invoice.total_amount or invoice.amount or Decimal("0")) - (invoice.paid_amount or Decimal("0"))
        if unpaid <= 0:
            continue

        total_unpaid += unpaid
        days_overdue = (today - invoice.due_date).days

        if days_overdue <= 30:
            aging_buckets["0-30"]["count"] += 1
            aging_buckets["0-30"]["amount"] += unpaid
        elif days_overdue <= 60:
            aging_buckets["31-60"]["count"] += 1
            aging_buckets["31-60"]["amount"] += unpaid
        elif days_overdue <= 90:
            aging_buckets["61-90"]["count"] += 1
            aging_buckets["61-90"]["amount"] += unpaid
        else:
            aging_buckets["90+"]["count"] += 1
            aging_buckets["90+"]["amount"] += unpaid

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_unpaid": float(total_unpaid),
            "aging_buckets": {
                "0-30": {
                    "count": aging_buckets["0-30"]["count"],
                    "amount": float(aging_buckets["0-30"]["amount"])
                },
                "31-60": {
                    "count": aging_buckets["31-60"]["count"],
                    "amount": float(aging_buckets["31-60"]["amount"])
                },
                "61-90": {
                    "count": aging_buckets["61-90"]["count"],
                    "amount": float(aging_buckets["61-90"]["amount"])
                },
                "90+": {
                    "count": aging_buckets["90+"]["count"],
                    "amount": float(aging_buckets["90+"]["amount"])
                }
            }
        }
    )


@router.get("/receivables/overdue", response_model=PaginatedResponse)
def get_overdue_receivables(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    min_overdue_days: Optional[int] = Query(None, description="最小逾期天数"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    逾期应收列表（已集成数据权限过滤）
    """
    from app.core.sales_permissions import filter_sales_finance_data_by_scope

    today = date.today()

    query = db.query(Invoice).filter(
        Invoice.status == "ISSUED",
        Invoice.payment_status.in_(["PENDING", "PARTIAL"]),
        Invoice.due_date.isnot(None),
        Invoice.due_date < today
    )

    # 应用数据权限过滤（发票使用财务数据权限）
    query = filter_sales_finance_data_by_scope(query, current_user, db, Invoice, "created_by")

    if customer_id:
        query = query.join(Contract).filter(Contract.customer_id == customer_id)

    if contract_id:
        query = query.filter(Invoice.contract_id == contract_id)

    total = query.count()
    invoices = apply_pagination(query.order_by(Invoice.due_date), pagination.offset, pagination.limit).all()

    items = []
    for invoice in invoices:
        contract = invoice.contract
        unpaid = (invoice.total_amount or invoice.amount or Decimal("0")) - (invoice.paid_amount or Decimal("0"))
        overdue_days = (today - invoice.due_date).days

        if min_overdue_days and overdue_days < min_overdue_days:
            continue

        items.append({
            "id": invoice.id,
            "invoice_code": invoice.invoice_code,
            "contract_id": invoice.contract_id,
            "contract_code": contract.contract_code if contract else None,
            "customer_id": contract.customer_id if contract else None,
            "customer_name": contract.customer.customer_name if contract and contract.customer else None,
            "invoice_amount": float(invoice.total_amount or invoice.amount or 0),
            "paid_amount": float(invoice.paid_amount or 0),
            "unpaid_amount": float(unpaid),
            "due_date": invoice.due_date,
            "overdue_days": overdue_days,
            "payment_status": invoice.payment_status,
        })

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.get("/receivables/summary", response_model=ResponseModel)
def get_receivables_summary(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    应收账款统计（已集成数据权限过滤）
    """
    from app.core.sales_permissions import filter_sales_finance_data_by_scope

    query = db.query(Invoice).filter(Invoice.status == "ISSUED")

    # 应用数据权限过滤（发票使用财务数据权限）
    query = filter_sales_finance_data_by_scope(query, current_user, db, Invoice, "created_by")

    if customer_id:
        query = query.join(Contract).filter(Contract.customer_id == customer_id)

    if contract_id:
        query = query.filter(Invoice.contract_id == contract_id)

    invoices = query.all()

    total_amount = Decimal("0")
    paid_amount = Decimal("0")
    unpaid_amount = Decimal("0")
    partial_amount = Decimal("0")
    overdue_amount = Decimal("0")
    overdue_count = 0

    today = date.today()

    for invoice in invoices:
        total = invoice.total_amount or invoice.amount or Decimal("0")
        paid = invoice.paid_amount or Decimal("0")
        unpaid = total - paid

        total_amount += total
        paid_amount += paid
        unpaid_amount += unpaid

        if invoice.payment_status == "PARTIAL":
            partial_amount += unpaid

        if invoice.due_date and invoice.due_date < today and invoice.payment_status in ["PENDING", "PARTIAL"]:
            overdue_amount += unpaid
            overdue_count += 1

    collection_rate = (paid_amount / total_amount * 100) if total_amount > 0 else Decimal("0")

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_amount": float(total_amount),
            "paid_amount": float(paid_amount),
            "unpaid_amount": float(unpaid_amount),
            "partial_amount": float(partial_amount),
            "overdue_amount": float(overdue_amount),
            "overdue_count": overdue_count,
            "collection_rate": float(collection_rate),
            "invoice_count": len(invoices),
            "paid_count": len([inv for inv in invoices if inv.payment_status == "PAID"]),
            "partial_count": len([inv for inv in invoices if inv.payment_status == "PARTIAL"]),
            "pending_count": len([inv for inv in invoices if inv.payment_status == "PENDING"]),
        }
    )
