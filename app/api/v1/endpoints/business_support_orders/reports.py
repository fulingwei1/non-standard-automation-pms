# -*- coding: utf-8 -*-
"""
商务支持模块 - 销售报表 API endpoints
"""

from typing import Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.api import deps
from app.models.user import User
from app.models.business_support import SalesOrder, BiddingProject
from app.models.sales import Contract, Invoice
from app.schemas.business_support import (
    SalesReportResponse, PaymentReportResponse,
    ContractReportResponse, InvoiceReportResponse
)
from app.schemas.common import ResponseModel

router = APIRouter()


# ==================== 销售报表 ====================


@router.get("/reports/sales-daily", response_model=ResponseModel[SalesReportResponse], summary="获取销售日报")
async def get_sales_daily_report(
    report_date: Optional[str] = Query(None, description="报表日期（YYYY-MM-DD格式），不提供则使用今天"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取销售日报"""
    try:
        # 确定报表日期
        if report_date:
            try:
                report_dt = datetime.strptime(report_date, "%Y-%m-%d").date()
            except:
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
            except:
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
        parse_month_string,
        calculate_month_range,
        calculate_contract_statistics,
        calculate_order_statistics,
        calculate_receipt_statistics,
        calculate_invoice_statistics,
        calculate_bidding_statistics
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


@router.get("/reports/payment", response_model=ResponseModel[PaymentReportResponse], summary="获取回款统计报表")
async def get_payment_report(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD格式）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取回款统计报表"""
    try:
        # 确定统计周期
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            except:
                raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")
        else:
            # 默认本月
            today = date.today()
            start_dt = date(today.year, today.month, 1)
            if today.month == 12:
                end_dt = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_dt = date(today.year, today.month + 1, 1) - timedelta(days=1)

        report_date_str = f"{start_dt.strftime('%Y-%m-%d')} ~ {end_dt.strftime('%Y-%m-%d')}"

        # 回款汇总
        total_planned_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount), 0) as planned
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
        """), {"start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")}).fetchone()
        total_planned_amount = Decimal(str(total_planned_result[0])) if total_planned_result and total_planned_result[0] else Decimal("0")

        total_actual_result = db.execute(text("""
            SELECT COALESCE(SUM(actual_amount), 0) as actual
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
            AND actual_amount > 0
        """), {"start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")}).fetchone()
        total_actual_amount = Decimal(str(total_actual_result[0])) if total_actual_result and total_actual_result[0] else Decimal("0")

        total_pending_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount - actual_amount), 0) as pending
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")}).fetchone()
        total_pending_amount = Decimal(str(total_pending_result[0])) if total_pending_result and total_pending_result[0] else Decimal("0")

        total_overdue_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount - actual_amount), 0) as overdue
            FROM project_payment_plans
            WHERE planned_date < :end_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"end_date": end_dt.strftime("%Y-%m-%d")}).fetchone()
        total_overdue_amount = Decimal(str(total_overdue_result[0])) if total_overdue_result and total_overdue_result[0] else Decimal("0")

        completion_rate = (total_actual_amount / total_planned_amount * 100) if total_planned_amount > 0 else Decimal("0")

        # 按类型统计（简化处理）
        prepayment_planned = Decimal("0")
        prepayment_actual = Decimal("0")
        delivery_payment_planned = Decimal("0")
        delivery_payment_actual = Decimal("0")
        acceptance_payment_planned = Decimal("0")
        acceptance_payment_actual = Decimal("0")
        warranty_payment_planned = Decimal("0")
        warranty_payment_actual = Decimal("0")

        # 按客户统计（前10名）
        top_customers_result = db.execute(text("""
            SELECT
                c.customer_name,
                COALESCE(SUM(ppp.actual_amount), 0) as receipt_amount
            FROM project_payment_plans ppp
            JOIN projects p ON ppp.project_id = p.id
            JOIN customers c ON p.customer_id = c.id
            WHERE ppp.planned_date >= :start_date
            AND ppp.planned_date <= :end_date
            AND ppp.actual_amount > 0
            GROUP BY c.id, c.customer_name
            ORDER BY receipt_amount DESC
            LIMIT 10
        """), {"start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")}).fetchall()

        top_customers = [
            {"customer_name": row[0], "receipt_amount": float(row[1])}
            for row in top_customers_result
        ]

        return ResponseModel(
            code=200,
            message="获取回款统计报表成功",
            data=PaymentReportResponse(
                report_date=report_date_str,
                report_type="payment",
                total_planned_amount=total_planned_amount,
                total_actual_amount=total_actual_amount,
                total_pending_amount=total_pending_amount,
                total_overdue_amount=total_overdue_amount,
                completion_rate=completion_rate,
                prepayment_planned=prepayment_planned,
                prepayment_actual=prepayment_actual,
                delivery_payment_planned=delivery_payment_planned,
                delivery_payment_actual=delivery_payment_actual,
                acceptance_payment_planned=acceptance_payment_planned,
                acceptance_payment_actual=acceptance_payment_actual,
                warranty_payment_planned=warranty_payment_planned,
                warranty_payment_actual=warranty_payment_actual,
                top_customers=top_customers
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取回款统计报表失败: {str(e)}")


@router.get("/reports/contract", response_model=ResponseModel[ContractReportResponse], summary="获取合同执行报表")
async def get_contract_report(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD格式）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取合同执行报表"""
    try:
        # 确定统计周期
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            except:
                raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")
        else:
            # 默认本月
            today = date.today()
            start_dt = date(today.year, today.month, 1)
            if today.month == 12:
                end_dt = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_dt = date(today.year, today.month + 1, 1) - timedelta(days=1)

        report_date_str = f"{start_dt.strftime('%Y-%m-%d')} ~ {end_dt.strftime('%Y-%m-%d')}"

        # 合同状态统计
        draft_count = db.query(Contract).filter(Contract.status == "DRAFT").count()
        signed_count = db.query(Contract).filter(Contract.status == "SIGNED").count()
        executing_count = db.query(Contract).filter(Contract.status == "EXECUTING").count()
        completed_count = db.query(Contract).filter(Contract.status == "COMPLETED").count()
        cancelled_count = db.query(Contract).filter(Contract.status == "CANCELLED").count()

        # 合同金额统计
        total_contracts = db.query(Contract).all()
        total_contract_amount = sum(c.contract_amount or Decimal("0") for c in total_contracts)

        signed_contracts = db.query(Contract).filter(Contract.status == "SIGNED").all()
        signed_amount = sum(c.contract_amount or Decimal("0") for c in signed_contracts)

        executing_contracts = db.query(Contract).filter(Contract.status == "EXECUTING").all()
        executing_amount = sum(c.contract_amount or Decimal("0") for c in executing_contracts)

        completed_contracts_objs = db.query(Contract).filter(Contract.status == "COMPLETED").all()
        completed_amount = sum(c.contract_amount or Decimal("0") for c in completed_contracts_objs)

        # 执行进度（简化处理，使用回款进度）
        avg_progress_result = db.execute(text("""
            SELECT AVG(
                CASE
                    WHEN SUM(ppp.planned_amount) > 0
                    THEN (SUM(ppp.actual_amount) / SUM(ppp.planned_amount)) * 100
                    ELSE 0
                END
            ) as avg_progress
            FROM contracts c
            LEFT JOIN projects p ON c.project_id = p.id
            LEFT JOIN project_payment_plans ppp ON p.id = ppp.project_id
            WHERE c.status IN ('SIGNED', 'EXECUTING')
            GROUP BY c.id
        """)).fetchone()
        average_execution_rate = Decimal(str(avg_progress_result[0])) if avg_progress_result and avg_progress_result[0] else Decimal("0")

        # 按客户统计（前10名）
        top_customers_result = db.execute(text("""
            SELECT
                c.customer_name,
                COALESCE(SUM(ct.contract_amount), 0) as contract_amount
            FROM contracts ct
            JOIN customers c ON ct.customer_id = c.id
            WHERE ct.signed_date >= :start_date
            AND ct.signed_date <= :end_date
            GROUP BY c.id, c.customer_name
            ORDER BY contract_amount DESC
            LIMIT 10
        """), {"start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")}).fetchall()

        top_customers = [
            {"customer_name": row[0], "contract_amount": float(row[1])}
            for row in top_customers_result
        ]

        return ResponseModel(
            code=200,
            message="获取合同执行报表成功",
            data=ContractReportResponse(
                report_date=report_date_str,
                report_type="contract",
                draft_count=draft_count,
                signed_count=signed_count,
                executing_count=executing_count,
                completed_count=completed_count,
                cancelled_count=cancelled_count,
                total_contract_amount=total_contract_amount,
                signed_amount=signed_amount,
                executing_amount=executing_amount,
                completed_amount=completed_amount,
                average_execution_rate=average_execution_rate,
                top_customers=top_customers
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取合同执行报表失败: {str(e)}")


@router.get("/reports/invoice", response_model=ResponseModel[InvoiceReportResponse], summary="获取开票统计报表")
async def get_invoice_report(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD格式）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取开票统计报表"""
    try:
        # 确定统计周期
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            except:
                raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")
        else:
            # 默认本月
            today = date.today()
            start_dt = date(today.year, today.month, 1)
            if today.month == 12:
                end_dt = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_dt = date(today.year, today.month + 1, 1) - timedelta(days=1)

        report_date_str = f"{start_dt.strftime('%Y-%m-%d')} ~ {end_dt.strftime('%Y-%m-%d')}"

        # 开票汇总
        invoices = (
            db.query(Invoice)
            .filter(
                func.date(Invoice.issue_date) >= start_dt,
                func.date(Invoice.issue_date) <= end_dt,
                Invoice.status == "ISSUED"
            )
            .all()
        )
        total_invoices_count = len(invoices)
        total_invoices_amount = sum(i.invoice_amount or Decimal("0") for i in invoices)
        total_tax_amount = sum(i.tax_amount or Decimal("0") for i in invoices)

        # 按类型统计（简化处理）
        special_invoice_count = 0
        special_invoice_amount = Decimal("0")
        normal_invoice_count = 0
        normal_invoice_amount = Decimal("0")
        electronic_invoice_count = 0
        electronic_invoice_amount = Decimal("0")

        for invoice in invoices:
            special_invoice_count += 1
            special_invoice_amount += invoice.invoice_amount or Decimal("0")

        # 开票及时率
        on_time_invoices_count = (
            db.query(Invoice)
            .filter(
                func.date(Invoice.issue_date) >= start_dt,
                func.date(Invoice.issue_date) <= end_dt,
                Invoice.status == "ISSUED"
            )
            .count()
        )

        overdue_invoices_count = 0  # 简化处理
        timeliness_rate = Decimal("100") if total_invoices_count > 0 else Decimal("0")

        # 按客户统计（前10名）
        top_customers_result = db.execute(text("""
            SELECT
                c.customer_name,
                COALESCE(SUM(i.invoice_amount), 0) as invoice_amount
            FROM invoices i
            JOIN contracts ct ON i.contract_id = ct.id
            JOIN customers c ON ct.customer_id = c.id
            WHERE i.issue_date >= :start_date
            AND i.issue_date <= :end_date
            AND i.status = 'ISSUED'
            GROUP BY c.id, c.customer_name
            ORDER BY invoice_amount DESC
            LIMIT 10
        """), {"start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")}).fetchall()

        top_customers = [
            {"customer_name": row[0], "invoice_amount": float(row[1])}
            for row in top_customers_result
        ]

        return ResponseModel(
            code=200,
            message="获取开票统计报表成功",
            data=InvoiceReportResponse(
                report_date=report_date_str,
                report_type="invoice",
                total_invoices_count=total_invoices_count,
                total_invoices_amount=total_invoices_amount,
                total_tax_amount=total_tax_amount,
                special_invoice_count=special_invoice_count,
                special_invoice_amount=special_invoice_amount,
                normal_invoice_count=normal_invoice_count,
                normal_invoice_amount=normal_invoice_amount,
                electronic_invoice_count=electronic_invoice_count,
                electronic_invoice_amount=electronic_invoice_amount,
                on_time_invoices_count=on_time_invoices_count,
                overdue_invoices_count=overdue_invoices_count,
                timeliness_rate=timeliness_rate,
                top_customers=top_customers
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取开票统计报表失败: {str(e)}")
