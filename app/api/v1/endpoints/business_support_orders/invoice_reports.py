# -*- coding: utf-8 -*-
"""
商务支持模块 - 开票统计报表 API endpoints
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.api import deps
from app.common.date_range import get_month_range
from app.models.sales import Invoice
from app.models.user import User
from app.schemas.business_support import InvoiceReportResponse
from app.schemas.common import ResponseModel

router = APIRouter()


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
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")
        else:
            # 默认本月
            today = date.today()
            start_dt, end_dt = get_month_range(today)

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
        total_invoices_amount = sum(i.amount or Decimal("0") for i in invoices)
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
            special_invoice_amount += invoice.amount or Decimal("0")

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
                COALESCE(SUM(i.amount), 0) as invoice_amount
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
