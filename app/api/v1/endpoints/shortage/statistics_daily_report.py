# -*- coding: utf-8 -*-
"""
缺料统计 - 缺料日报
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.shortage import ShortageDailyReport, ShortageReport
from app.models.user import User
from app.schemas.common import ResponseModel
from .statistics_helpers import _build_shortage_daily_report

router = APIRouter()


@router.get("/shortage/daily-report", response_model=ResponseModel)
def get_daily_report(
    db: Session = Depends(deps.get_db),
    report_date: Optional[date] = Query(None, description="报表日期（默认：今天）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料日报
    """
    if not report_date:
        report_date = date.today()

    # 统计当日缺料上报
    daily_reports = db.query(ShortageReport).filter(
        func.date(ShortageReport.report_time) == report_date
    ).all()

    # 按紧急程度统计
    by_urgent = {}
    for report in daily_reports:
        level = report.urgent_level
        if level not in by_urgent:
            by_urgent[level] = 0
        by_urgent[level] += 1

    # 按状态统计
    by_status = {}
    for report in daily_reports:
        status = report.status
        if status not in by_status:
            by_status[status] = 0
        by_status[status] += 1

    # 按物料统计
    by_material = {}
    for report in daily_reports:
        material_key = f"{report.material_id}_{report.material_name}"
        if material_key not in by_material:
            by_material[material_key] = {
                "material_id": report.material_id,
                "material_name": report.material_name,
                "count": 0,
                "total_shortage_qty": 0.0
            }
        by_material[material_key]["count"] += 1
        by_material[material_key]["total_shortage_qty"] += float(report.shortage_qty)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "report_date": str(report_date),
            "total_reports": len(daily_reports),
            "by_urgent": by_urgent,
            "by_status": by_status,
            "by_material": list(by_material.values())
        }
    )


@router.get("/shortage/daily-report/latest", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_latest_shortage_daily_report(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最新缺料日报（定时生成）
    """
    latest_date = db.query(func.max(ShortageDailyReport.report_date)).scalar()
    if not latest_date:
        return ResponseModel(data=None)

    report = db.query(ShortageDailyReport).filter(
        ShortageDailyReport.report_date == latest_date
    ).first()

    if not report:
        return ResponseModel(data=None)

    return ResponseModel(data=_build_shortage_daily_report(report))


@router.get("/shortage/daily-report/by-date", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_shortage_daily_report_by_date(
    *,
    db: Session = Depends(deps.get_db),
    report_date: date = Query(..., description="报表日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    按日期获取缺料日报（定时生成的数据）
    """
    report = db.query(ShortageDailyReport).filter(
        ShortageDailyReport.report_date == report_date
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="指定日期不存在缺料日报")

    return ResponseModel(data=_build_shortage_daily_report(report))
