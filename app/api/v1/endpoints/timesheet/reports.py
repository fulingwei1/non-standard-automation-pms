# -*- coding: utf-8 -*-
"""
工时报表端点

提供工时报表生成和查询功能
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.date_range import get_month_range_by_ym
from app.core import security
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/reports/summary", response_model=ResponseModel)
def get_timesheet_report_summary(
    year: int = Query(..., description="年份"),
    month: int = Query(..., description="月份"),
    department_id: Optional[int] = Query(None, description="部门ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工时报表汇总
    """
    month_start, month_end = get_month_range_by_ym(year, month)

    base_filter = [
        Timesheet.work_date >= month_start,
        Timesheet.work_date <= month_end,
        Timesheet.status == "APPROVED",
    ]
    if department_id:
        base_filter.append(Timesheet.department_id == department_id)

    # 汇总统计
    result = db.query(
        func.coalesce(func.sum(Timesheet.hours), 0).label("total_hours"),
        func.count(func.distinct(Timesheet.user_id)).label("total_users"),
        func.count(Timesheet.id).label("total_records"),
        func.count(func.distinct(Timesheet.project_id)).label("total_projects"),
    ).filter(*base_filter).first()

    # 按用户汇总
    user_rows = db.query(
        Timesheet.user_id,
        Timesheet.user_name,
        func.coalesce(func.sum(Timesheet.hours), 0).label("hours"),
        func.count(Timesheet.id).label("records"),
    ).filter(
        *base_filter
    ).group_by(
        Timesheet.user_id, Timesheet.user_name
    ).order_by(func.sum(Timesheet.hours).desc()).all()

    users = [
        {
            "user_id": row.user_id,
            "user_name": row.user_name,
            "hours": float(row.hours),
            "records": row.records,
        }
        for row in user_rows
    ]

    return ResponseModel(
        code=200,
        message="success",
        data={
            "year": year,
            "month": month,
            "total_hours": float(result.total_hours) if result else 0,
            "total_users": result.total_users if result else 0,
            "total_records": result.total_records if result else 0,
            "total_projects": result.total_projects if result else 0,
            "department_id": department_id,
            "users": users,
        },
    )


@router.get("/reports/detail", response_model=ResponseModel)
def get_timesheet_report_detail(
    year: int = Query(..., description="年份"),
    month: int = Query(..., description="月份"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工时报表明细
    """
    month_start, month_end = get_month_range_by_ym(year, month)

    query = db.query(Timesheet).filter(
        Timesheet.work_date >= month_start,
        Timesheet.work_date <= month_end,
        Timesheet.status == "APPROVED",
    )

    if user_id:
        query = query.filter(Timesheet.user_id == user_id)
    if project_id:
        query = query.filter(Timesheet.project_id == project_id)

    records = query.order_by(Timesheet.work_date.desc(), Timesheet.user_id).all()

    items = [
        {
            "id": r.id,
            "timesheet_no": r.timesheet_no,
            "user_id": r.user_id,
            "user_name": r.user_name,
            "department_name": r.department_name,
            "project_id": r.project_id,
            "project_code": r.project_code,
            "project_name": r.project_name,
            "work_date": r.work_date.isoformat() if r.work_date else None,
            "hours": float(r.hours) if r.hours else 0,
            "overtime_type": r.overtime_type,
            "work_content": r.work_content,
        }
        for r in records
    ]

    return ResponseModel(
        code=200,
        message="success",
        data={
            "year": year,
            "month": month,
            "records": items,
        },
    )
