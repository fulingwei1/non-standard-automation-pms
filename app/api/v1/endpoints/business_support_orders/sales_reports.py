# -*- coding: utf-8 -*-
"""
商务支持模块 - 销售报表 API endpoints（日报、周报、月报）
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.models.business_support import BiddingProject, SalesOrder
from app.models.sales import Contract, Invoice
from app.models.user import User
from app.schemas.business_support import SalesReportResponse
from app.schemas.common import ResponseModel

router = APIRouter()


def _parse_week_string(week: str):
    """解析周字符串，返回(年, 周数, 周开始日期, 周结束日期)"""
    year, week_num = map(int, week.split("-W"))
    jan1 = date(year, 1, 1)
    days_offset = (week_num - 1) * 7
    week_start = jan1 + timedelta(days=-jan1.weekday() + days_offset)
    week_end = week_start + timedelta(days=6)
    return year, week_num, week_start, week_end


def _get_current_week_range():
    """获取当前周范围"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    year = today.year
    week_num = (today - date(today.year, 1, 1)).days // 7 + 1
    return year, week_num, week_start, week_end


def _calculate_contract_stats(db: Session, start_date: date, end_date: date):
    """计算合同统计"""
    new_contracts = db.query(Contract).filter(
        Contract.signed_date >= start_date,
        Contract.signed_date <= end_date,
        Contract.status.in_(["SIGNED", "EXECUTING"])
    ).all()
    return {
        'new_count': len(new_contracts),
        'new_amount': sum(c.contract_amount or Decimal("0") for c in new_contracts),
        'active_count': db.query(Contract).filter(Contract.status.in_(["SIGNED", "EXECUTING"])).count(),
        'completed_count': db.query(Contract).filter(Contract.status == "COMPLETED").count()
    }


def _calculate_order_stats(db: Session, start_date: date, end_date: date):
    """计算订单统计"""
    new_orders = db.query(SalesOrder).filter(
        func.date(SalesOrder.created_at) >= start_date,
        func.date(SalesOrder.created_at) <= end_date
    ).all()
    return {
        'new_count': len(new_orders),
        'new_amount': sum(o.order_amount or Decimal("0") for o in new_orders)
    }


def _calculate_receipt_stats(db: Session, start_date: date, end_date: date):
    """计算回款统计"""
    from sqlalchemy import text
    
    params = {"start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d")}

    planned = db.execute(text("""
        SELECT COALESCE(SUM(planned_amount), 0) FROM project_payment_plans
        WHERE planned_date >= :start_date AND planned_date <= :end_date
    """), params).fetchone()
    planned_amount = Decimal(str(planned[0])) if planned and planned[0] else Decimal("0")

    actual = db.execute(text("""
        SELECT COALESCE(SUM(actual_amount), 0) FROM project_payment_plans
        WHERE planned_date >= :start_date AND planned_date <= :end_date AND actual_amount > 0
    """), params).fetchone()
    actual_amount = Decimal(str(actual[0])) if actual and actual[0] else Decimal("0")

    overdue = db.execute(text("""
        SELECT COALESCE(SUM(planned_amount - actual_amount), 0) FROM project_payment_plans
        WHERE planned_date < :end_date AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
    """), {"end_date": end_date.strftime("%Y-%m-%d")}).fetchone()
    overdue_amount = Decimal(str(overdue[0])) if overdue and overdue[0] else Decimal("0")

    return {
        'planned': planned_amount,
        'actual': actual_amount,
        'rate': (actual_amount / planned_amount * 100) if planned_amount > 0 else Decimal("0"),
        'overdue': overdue_amount
    }


def _calculate_invoice_stats(db: Session, start_date: date, end_date: date):
    """计算开票统计"""
    from sqlalchemy import text
    
    invoices = db.query(Invoice).filter(
        func.date(Invoice.issue_date) >= start_date,
        func.date(Invoice.issue_date) <= end_date,
        Invoice.status == "ISSUED"
    ).all()
    invoices_count = len(invoices)
    invoices_amount = sum(i.invoice_amount or Decimal("0") for i in invoices)

    total_needed = db.execute(text("""
        SELECT COUNT(*) FROM project_payment_plans
        WHERE planned_date <= :end_date AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
    """), {"end_date": end_date.strftime("%Y-%m-%d")}).fetchone()
    rate = (Decimal(invoices_count) / Decimal(total_needed[0]) * 100) if total_needed and total_needed[0] > 0 else Decimal("0")

    return {'count': invoices_count, 'amount': invoices_amount, 'rate': rate}


def _calculate_bidding_stats(db: Session, start_date: date, end_date: date):
    """计算投标统计"""
    new_bidding = db.query(BiddingProject).filter(
        func.date(BiddingProject.created_at) >= start_date,
        func.date(BiddingProject.created_at) <= end_date
    ).count()

    won_bidding = db.query(BiddingProject).filter(
        BiddingProject.result_date >= start_date,
        BiddingProject.result_date <= end_date,
        BiddingProject.bid_result == "won"
    ).count()

    total = db.query(BiddingProject).count()
    win_rate = (Decimal(won_bidding) / Decimal(total) * 100) if total > 0 else Decimal("0")

    return {'new_count': new_bidding, 'won_count': won_bidding, 'win_rate': win_rate}


@router.get("/reports/sales-daily", response_model=ResponseModel[SalesReportResponse], summary="获取销售日报")
async def get_sales_daily_report(
    report_date: Optional[str] = Query(None, description="报表日期（YYYY-MM-DD格式），不提供则使用今天"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取销售日报"""
    from sqlalchemy import text
    
    try:
        # 确定报表日期
        if report_date:
            try:
                report_dt = datetime.strptime(report_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")
        else:
            report_dt = date.today()

        report_date_str = report_dt.strftime("%Y-%m-%d")

        # 1. 合同统计
        new_contracts = (
            db.query(Contract)
            .filter(
                func.date(Contract.signed_date) == report_dt,
                Contract.status.in_(["SIGNED", "EXECUTING"])
            )
            .all()
        )
        new_contracts_count = len(new_contracts)
        new_contracts_amount = sum(c.contract_amount or Decimal("0") for c in new_contracts)

        active_contracts = (
            db.query(Contract)
            .filter(Contract.status.in_(["SIGNED", "EXECUTING"]))
            .count()
        )

        completed_contracts = (
            db.query(Contract)
            .filter(Contract.status == "COMPLETED")
            .count()
        )

        # 2. 订单统计
        new_orders = (
            db.query(SalesOrder)
            .filter(func.date(SalesOrder.created_at) == report_dt)
            .all()
        )
        new_orders_count = len(new_orders)
        new_orders_amount = sum(o.order_amount or Decimal("0") for o in new_orders)

        # 3. 回款统计
        planned_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount), 0) as planned
            FROM project_payment_plans
            WHERE planned_date = :report_date
        """), {"report_date": report_date_str}).fetchone()
        planned_receipt_amount = Decimal(str(planned_result[0])) if planned_result and planned_result[0] else Decimal("0")

        actual_result = db.execute(text("""
            SELECT COALESCE(SUM(actual_amount), 0) as actual
            FROM project_payment_plans
            WHERE planned_date = :report_date
            AND actual_amount > 0
        """), {"report_date": report_date_str}).fetchone()
        actual_receipt_amount = Decimal(str(actual_result[0])) if actual_result and actual_result[0] else Decimal("0")

        receipt_completion_rate = (actual_receipt_amount / planned_receipt_amount * 100) if planned_receipt_amount > 0 else Decimal("0")

        overdue_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount - actual_amount), 0) as overdue
            FROM project_payment_plans
            WHERE planned_date < :report_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"report_date": report_date_str}).fetchone()
        overdue_amount = Decimal(str(overdue_result[0])) if overdue_result and overdue_result[0] else Decimal("0")

        # 4. 开票统计
        invoices = (
            db.query(Invoice)
            .filter(func.date(Invoice.issue_date) == report_dt, Invoice.status == "ISSUED")
            .all()
        )
        invoices_count = len(invoices)
        invoices_amount = sum(i.invoice_amount or Decimal("0") for i in invoices)

        # 计算开票率（简化处理）
        total_needed = db.execute(text("""
            SELECT COUNT(*) as count
            FROM project_payment_plans
            WHERE planned_date <= :report_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"report_date": report_date_str}).fetchone()
        invoice_rate = (Decimal(invoices_count) / Decimal(total_needed[0]) * 100) if total_needed and total_needed[0] > 0 else Decimal("0")

        # 5. 投标统计
        new_bidding = (
            db.query(BiddingProject)
            .filter(func.date(BiddingProject.created_at) == report_dt)
            .count()
        )

        won_bidding = (
            db.query(BiddingProject)
            .filter(
                func.date(BiddingProject.result_date) == report_dt,
                BiddingProject.bid_result == "won"
            )
            .count()
        )

        total_bidding = db.query(BiddingProject).count()
        bidding_win_rate = (Decimal(won_bidding) / Decimal(total_bidding) * 100) if total_bidding > 0 else Decimal("0")

        return ResponseModel(
            code=200,
            message="获取销售日报成功",
            data=SalesReportResponse(
                report_date=report_date_str,
                report_type="daily",
                new_contracts_count=new_contracts_count,
                new_contracts_amount=new_contracts_amount,
                active_contracts_count=active_contracts,
                completed_contracts_count=completed_contracts,
                new_orders_count=new_orders_count,
                new_orders_amount=new_orders_amount,
                planned_receipt_amount=planned_receipt_amount,
                actual_receipt_amount=actual_receipt_amount,
                receipt_completion_rate=receipt_completion_rate,
                overdue_amount=overdue_amount,
                invoices_count=invoices_count,
                invoices_amount=invoices_amount,
                invoice_rate=invoice_rate,
                new_bidding_count=new_bidding,
                won_bidding_count=won_bidding,
                bidding_win_rate=bidding_win_rate
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售日报失败: {str(e)}")


@router.get("/reports/sales-weekly", response_model=ResponseModel[SalesReportResponse], summary="获取销售周报")
async def get_sales_weekly_report(
    week: Optional[str] = Query(None, description="周（YYYY-WW格式），不提供则使用当前周"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取销售周报"""
    try:
        # 确定报表周期
        if week:
            try:
                year, week_num, week_start, week_end = _parse_week_string(week)
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="周格式错误，应为YYYY-WW")
        else:
            year, week_num, week_start, week_end = _get_current_week_range()

        week_str = f"{year}-W{week_num:02d}"

        # 使用辅助函数计算各类统计
        contract_stats = _calculate_contract_stats(db, week_start, week_end)
        order_stats = _calculate_order_stats(db, week_start, week_end)
        receipt_stats = _calculate_receipt_stats(db, week_start, week_end)
        invoice_stats = _calculate_invoice_stats(db, week_start, week_end)
        bidding_stats = _calculate_bidding_stats(db, week_start, week_end)

        return ResponseModel(
            code=200,
            message="获取销售周报成功",
            data=SalesReportResponse(
                report_date=week_str,
                report_type="weekly",
                new_contracts_count=contract_stats['new_count'],
                new_contracts_amount=contract_stats['new_amount'],
                active_contracts_count=contract_stats['active_count'],
                completed_contracts_count=contract_stats['completed_count'],
                new_orders_count=order_stats['new_count'],
                new_orders_amount=order_stats['new_amount'],
                planned_receipt_amount=receipt_stats['planned'],
                actual_receipt_amount=receipt_stats['actual'],
                receipt_completion_rate=receipt_stats['rate'],
                overdue_amount=receipt_stats['overdue'],
                invoices_count=invoice_stats['count'],
                invoices_amount=invoice_stats['amount'],
                invoice_rate=invoice_stats['rate'],
                new_bidding_count=bidding_stats['new_count'],
                won_bidding_count=bidding_stats['won_count'],
                bidding_win_rate=bidding_stats['win_rate']
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售周报失败: {str(e)}")


@router.get("/reports/sales-monthly", response_model=ResponseModel[SalesReportResponse], summary="获取销售月报")
async def get_sales_monthly_report(
    month: Optional[str] = Query(None, description="月份（YYYY-MM格式），不提供则使用当前月份"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取销售月报"""
    from app.services.sales_monthly_report_service import (
        calculate_bidding_statistics,
        calculate_contract_statistics,
        calculate_invoice_statistics,
        calculate_month_range,
        calculate_order_statistics,
        calculate_receipt_statistics,
        parse_month_string,
    )

    try:
        # 解析月份并计算日期范围
        year, month_num = parse_month_string(month)
        month_start, month_end = calculate_month_range(year, month_num)
        month_str = f"{year}-{month_num:02d}"

        # 计算各项统计
        contract_stats = calculate_contract_statistics(db, month_start, month_end)
        order_stats = calculate_order_statistics(db, month_start, month_end)
        receipt_stats = calculate_receipt_statistics(db, month_start, month_end)
        invoice_stats = calculate_invoice_statistics(db, month_start, month_end)
        bidding_stats = calculate_bidding_statistics(db, month_start, month_end)

        return ResponseModel(
            code=200,
            message="获取销售月报成功",
            data=SalesReportResponse(
                report_date=month_str,
                report_type="monthly",
                new_contracts_count=contract_stats["new_contracts_count"],
                new_contracts_amount=contract_stats["new_contracts_amount"],
                active_contracts_count=contract_stats["active_contracts"],
                completed_contracts_count=contract_stats["completed_contracts"],
                new_orders_count=order_stats["new_orders_count"],
                new_orders_amount=order_stats["new_orders_amount"],
                planned_receipt_amount=receipt_stats["planned_receipt_amount"],
                actual_receipt_amount=receipt_stats["actual_receipt_amount"],
                receipt_completion_rate=receipt_stats["receipt_completion_rate"],
                overdue_amount=receipt_stats["overdue_amount"],
                invoices_count=invoice_stats["invoices_count"],
                invoices_amount=invoice_stats["invoices_amount"],
                invoice_rate=invoice_stats["invoice_rate"],
                new_bidding_count=bidding_stats["new_bidding"],
                won_bidding_count=bidding_stats["won_bidding"],
                bidding_win_rate=bidding_stats["bidding_win_rate"]
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售月报失败: {str(e)}")
