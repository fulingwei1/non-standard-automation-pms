# -*- coding: utf-8 -*-
"""
商务支持模块 - 回款统计报表 API endpoints
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.business_support import PaymentReportResponse
from app.schemas.common import ResponseModel

router = APIRouter()


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
            except ValueError:
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
