# -*- coding: utf-8 -*-
"""
销售月报服务
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.business_support import BiddingProject, SalesOrder
from app.models.sales import Contract, Invoice


def parse_month_string(month: Optional[str]) -> Tuple[int, int]:
    """
    解析月份字符串

    Returns:
        Tuple[int, int]: (年份, 月份)
    """
    if month:
        try:
            year, month_num = map(int, month.split("-"))
            return year, month_num
        except (ValueError, TypeError):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="月份格式错误，应为YYYY-MM")
    else:
        today = date.today()
        return today.year, today.month


def calculate_month_range(year: int, month_num: int) -> Tuple[date, date]:
    """
    计算月份的开始和结束日期

    Returns:
        Tuple[date, date]: (开始日期, 结束日期)
    """
    month_start = date(year, month_num, 1)
    if month_num == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month_num + 1, 1) - timedelta(days=1)

    return month_start, month_end


def calculate_contract_statistics(
    db: Session,
    month_start: date,
    month_end: date
) -> Dict[str, Any]:
    """
    计算合同统计

    Returns:
        Dict: 合同统计数据
    """
    new_contracts = (
        db.query(Contract)
        .filter(
            Contract.signed_date >= month_start,
            Contract.signed_date <= month_end,
            Contract.status.in_(["SIGNED", "EXECUTING"])
        )
        .all()
    )

    new_contracts_count = len(new_contracts)
    new_contracts_amount = sum(c.contract_amount or Decimal("0") for c in new_contracts)

    active_contracts = db.query(Contract).filter(Contract.status.in_(["SIGNED", "EXECUTING"])).count()
    completed_contracts = db.query(Contract).filter(Contract.status == "COMPLETED").count()

    return {
        "new_contracts_count": new_contracts_count,
        "new_contracts_amount": new_contracts_amount,
        "active_contracts": active_contracts,
        "completed_contracts": completed_contracts,
    }


def calculate_order_statistics(
    db: Session,
    month_start: date,
    month_end: date
) -> Dict[str, Any]:
    """
    计算订单统计

    Returns:
        Dict: 订单统计数据
    """
    new_orders = (
        db.query(SalesOrder)
        .filter(
            func.date(SalesOrder.created_at) >= month_start,
            func.date(SalesOrder.created_at) <= month_end
        )
        .all()
    )

    new_orders_count = len(new_orders)
    new_orders_amount = sum(o.order_amount or Decimal("0") for o in new_orders)

    return {
        "new_orders_count": new_orders_count,
        "new_orders_amount": new_orders_amount,
    }


def calculate_receipt_statistics(
    db: Session,
    month_start: date,
    month_end: date
) -> Dict[str, Any]:
    """
    计算回款统计

    Returns:
        Dict: 回款统计数据
    """
    planned_result = db.execute(text("""
        SELECT COALESCE(SUM(planned_amount), 0) as planned
        FROM project_payment_plans
        WHERE planned_date >= :start_date
        AND planned_date <= :end_date
    """), {"start_date": month_start.strftime("%Y-%m-%d"), "end_date": month_end.strftime("%Y-%m-%d")}).fetchone()

    planned_receipt_amount = Decimal(str(planned_result[0])) if planned_result and planned_result[0] else Decimal("0")

    actual_result = db.execute(text("""
        SELECT COALESCE(SUM(actual_amount), 0) as actual
        FROM project_payment_plans
        WHERE planned_date >= :start_date
        AND planned_date <= :end_date
        AND actual_amount > 0
    """), {"start_date": month_start.strftime("%Y-%m-%d"), "end_date": month_end.strftime("%Y-%m-%d")}).fetchone()

    actual_receipt_amount = Decimal(str(actual_result[0])) if actual_result and actual_result[0] else Decimal("0")

    receipt_completion_rate = (actual_receipt_amount / planned_receipt_amount * 100) if planned_receipt_amount > 0 else Decimal("0")

    overdue_result = db.execute(text("""
        SELECT COALESCE(SUM(planned_amount - actual_amount), 0) as overdue
        FROM project_payment_plans
        WHERE planned_date < :end_date
        AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
    """), {"end_date": month_end.strftime("%Y-%m-%d")}).fetchone()

    overdue_amount = Decimal(str(overdue_result[0])) if overdue_result and overdue_result[0] else Decimal("0")

    return {
        "planned_receipt_amount": planned_receipt_amount,
        "actual_receipt_amount": actual_receipt_amount,
        "receipt_completion_rate": receipt_completion_rate,
        "overdue_amount": overdue_amount,
    }


def calculate_invoice_statistics(
    db: Session,
    month_start: date,
    month_end: date
) -> Dict[str, Any]:
    """
    计算开票统计

    Returns:
        Dict: 开票统计数据
    """
    invoices = (
        db.query(Invoice)
        .filter(
            func.date(Invoice.issue_date) >= month_start,
            func.date(Invoice.issue_date) <= month_end,
            Invoice.status == "ISSUED"
        )
        .all()
    )

    invoices_count = len(invoices)
    invoices_amount = sum(i.invoice_amount or Decimal("0") for i in invoices)

    total_needed = db.execute(text("""
        SELECT COUNT(*) as count
        FROM project_payment_plans
        WHERE planned_date <= :end_date
        AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
    """), {"end_date": month_end.strftime("%Y-%m-%d")}).fetchone()

    invoice_rate = (Decimal(invoices_count) / Decimal(total_needed[0]) * 100) if total_needed and total_needed[0] > 0 else Decimal("0")

    return {
        "invoices_count": invoices_count,
        "invoices_amount": invoices_amount,
        "invoice_rate": invoice_rate,
    }


def calculate_bidding_statistics(
    db: Session,
    month_start: date,
    month_end: date
) -> Dict[str, Any]:
    """
    计算投标统计

    Returns:
        Dict: 投标统计数据
    """
    new_bidding = (
        db.query(BiddingProject)
        .filter(
            func.date(BiddingProject.created_at) >= month_start,
            func.date(BiddingProject.created_at) <= month_end
        )
        .count()
    )

    won_bidding = (
        db.query(BiddingProject)
        .filter(
            BiddingProject.result_date >= month_start,
            BiddingProject.result_date <= month_end,
            BiddingProject.bid_result == "won"
        )
        .count()
    )

    total_bidding = db.query(BiddingProject).count()
    bidding_win_rate = (Decimal(won_bidding) / Decimal(total_bidding) * 100) if total_bidding > 0 else Decimal("0")

    return {
        "new_bidding": new_bidding,
        "won_bidding": won_bidding,
        "bidding_win_rate": bidding_win_rate,
    }
