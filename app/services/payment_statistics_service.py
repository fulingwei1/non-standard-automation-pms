# -*- coding: utf-8 -*-
"""
回款统计服务
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.sales import Contract, Invoice


def build_invoice_query(
    db: Session,
    customer_id: Optional[int],
    start_date: Optional[date],
    end_date: Optional[date]
):
    """
    构建发票查询

    Returns:
        Query: SQLAlchemy查询对象
    """
    query = db.query(Invoice).filter(Invoice.status == "ISSUED")

    if customer_id:
        query = query.join(Contract).filter(Contract.customer_id == customer_id)

    if start_date:
        query = query.filter(
            or_(
                and_(
                    Invoice.issue_date.isnot(None),
                    Invoice.issue_date >= start_date
                ),
                and_(
                    Invoice.issue_date.is_(None),
                    Invoice.created_at >= datetime.combine(start_date, datetime.min.time())
                )
            )
        )

    if end_date:
        query = query.filter(
            or_(
                and_(
                    Invoice.issue_date.isnot(None),
                    Invoice.issue_date <= end_date
                ),
                and_(
                    Invoice.issue_date.is_(None),
                    Invoice.created_at <= datetime.combine(end_date, datetime.max.time())
                )
            )
        )

    return query


def calculate_monthly_statistics(invoices: List[Invoice]) -> Dict[str, Dict[str, Any]]:
    """
    按月份统计

    Returns:
        Dict[str, Dict]: 月份统计数据
    """
    monthly_stats = {}

    for invoice in invoices:
        if invoice.issue_date:
            month_key = invoice.issue_date.strftime("%Y-%m")
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {"invoiced": Decimal("0"), "paid": Decimal("0"), "count": 0}

            total = invoice.total_amount or invoice.amount or Decimal("0")
            paid = invoice.paid_amount or Decimal("0")

            monthly_stats[month_key]["invoiced"] += total
            monthly_stats[month_key]["paid"] += paid
            monthly_stats[month_key]["count"] += 1

    return monthly_stats


def calculate_customer_statistics(invoices: List[Invoice]) -> Dict[int, Dict[str, Any]]:
    """
    按客户统计

    Returns:
        Dict[int, Dict]: 客户统计数据
    """
    customer_stats = {}

    for invoice in invoices:
        if contract := invoice.contract:
            customer_id_key = contract.customer_id
            customer_name = contract.customer.customer_name if contract.customer else "未知客户"

            if customer_id_key not in customer_stats:
                customer_stats[customer_id_key] = {
                    "customer_id": customer_id_key,
                    "customer_name": customer_name,
                    "invoiced": Decimal("0"),
                    "paid": Decimal("0"),
                    "unpaid": Decimal("0"),
                    "count": 0
                }

            total = invoice.total_amount or invoice.amount or Decimal("0")
            paid = invoice.paid_amount or Decimal("0")
            unpaid = total - paid

            customer_stats[customer_id_key]["invoiced"] += total
            customer_stats[customer_id_key]["paid"] += paid
            customer_stats[customer_id_key]["unpaid"] += unpaid
            customer_stats[customer_id_key]["count"] += 1

    return customer_stats


def calculate_status_statistics(invoices: List[Invoice]) -> Dict[str, Dict[str, Any]]:
    """
    按状态统计

    Returns:
        Dict[str, Dict]: 状态统计数据
    """
    status_stats = {
        "PAID": {"count": 0, "amount": Decimal("0")},
        "PARTIAL": {"count": 0, "amount": Decimal("0")},
        "PENDING": {"count": 0, "amount": Decimal("0")},
    }

    for invoice in invoices:
        status = invoice.payment_status or "PENDING"
        total = invoice.total_amount or invoice.amount or Decimal("0")

        if status in status_stats:
            status_stats[status]["count"] += 1
            status_stats[status]["amount"] += total

    return status_stats


def calculate_overdue_amount(invoices: List[Invoice], today: date) -> Decimal:
    """
    计算逾期金额

    Returns:
        Decimal: 逾期金额
    """
    total_overdue = Decimal("0")

    for invoice in invoices:
        if invoice.due_date and invoice.due_date < today:
            if invoice.payment_status in ["PENDING", "PARTIAL"]:
                total = invoice.total_amount or invoice.amount or Decimal("0")
                paid = invoice.paid_amount or Decimal("0")
                unpaid = total - paid
                total_overdue += unpaid

    return total_overdue


def build_monthly_list(monthly_stats: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    构建月度统计列表

    Returns:
        List[Dict]: 月度统计列表
    """
    return [
        {
            "month": month,
            "invoiced": float(stats["invoiced"]),
            "paid": float(stats["paid"]),
            "unpaid": float(stats["invoiced"] - stats["paid"]),
            "collection_rate": float((stats["paid"] / stats["invoiced"] * 100) if stats["invoiced"] > 0 else 0),
            "count": stats["count"]
        }
        for month, stats in sorted(monthly_stats.items())
    ]


def build_customer_list(customer_stats: Dict[int, Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """
    构建客户统计列表

    Returns:
        List[Dict]: 客户统计列表
    """
    return [
        {
            "customer_id": stats["customer_id"],
            "customer_name": stats["customer_name"],
            "invoiced": float(stats["invoiced"]),
            "paid": float(stats["paid"]),
            "unpaid": float(stats["unpaid"]),
            "collection_rate": float((stats["paid"] / stats["invoiced"] * 100) if stats["invoiced"] > 0 else 0),
            "count": stats["count"]
        }
        for stats in sorted(customer_stats.values(), key=lambda x: x["unpaid"], reverse=True)[:limit]
    ]
