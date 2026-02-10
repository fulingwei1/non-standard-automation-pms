# -*- coding: utf-8 -*-
"""
商务支持模块 - 合同执行报表 API endpoints
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.common.date_range import get_month_range
from app.models.sales import Contract
from app.models.user import User
from app.schemas.business_support import ContractReportResponse
from app.schemas.common import ResponseModel

router = APIRouter()


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
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")
        else:
            # 默认本月
            today = date.today()
            start_dt, end_dt = get_month_range(today)

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
