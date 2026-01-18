# -*- coding: utf-8 -*-
"""
缺料统计 - 供应商交期分析
"""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.shortage import MaterialArrival
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/shortage/supplier-delivery", response_model=ResponseModel)
def get_supplier_delivery_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    supplier_id: Optional[int] = Query(None, description="供应商ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    供应商交期分析
    """
    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    query = db.query(MaterialArrival).filter(
        MaterialArrival.expected_date >= start_date,
        MaterialArrival.expected_date <= end_date
    )

    if supplier_id:
        query = query.filter(MaterialArrival.supplier_id == supplier_id)

    arrivals = query.all()

    # 按供应商统计
    supplier_stats = {}
    for arrival in arrivals:
        if arrival.supplier_id:
            supplier_key = f"{arrival.supplier_id}_{arrival.supplier_name}"
            if supplier_key not in supplier_stats:
                supplier_stats[supplier_key] = {
                    "supplier_id": arrival.supplier_id,
                    "supplier_name": arrival.supplier_name,
                    "total_orders": 0,
                    "on_time": 0,
                    "delayed": 0,
                    "avg_delay_days": 0.0
                }

            supplier_stats[supplier_key]["total_orders"] += 1
            if arrival.is_delayed:
                supplier_stats[supplier_key]["delayed"] += 1
                supplier_stats[supplier_key]["avg_delay_days"] += arrival.delay_days or 0
            else:
                supplier_stats[supplier_key]["on_time"] += 1

    # 计算平均延迟天数
    for key, stats in supplier_stats.items():
        if stats["delayed"] > 0:
            stats["avg_delay_days"] = round(stats["avg_delay_days"] / stats["delayed"], 2)
        stats["on_time_rate"] = round(stats["on_time"] / stats["total_orders"] * 100, 2) if stats["total_orders"] > 0 else 0.0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "supplier_stats": list(supplier_stats.values())
        }
    )
