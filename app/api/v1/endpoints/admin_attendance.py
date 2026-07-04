# -*- coding: utf-8 -*-
"""Administrative attendance compatibility routes.

The current attendance page consumes ``/admin/attendance``.  The project does
not yet have a production attendance domain behind these admin routes, so the
compatibility endpoints return explicit empty states instead of synthesizing
attendance, leave, late, or punch records from the employee roster.
"""

from __future__ import annotations

from datetime import date, datetime
from io import StringIO
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api import deps
from app.models.organization import Employee
from app.models.user import User

router = APIRouter()


def _active_employee_total(db: Session) -> int:
    return db.query(Employee).filter(Employee.is_active.is_(True)).count()


def _empty_attendance_payload(db: Session, date_filter: Optional[str] = None) -> Dict[str, Any]:
    return {
        "items": [],
        "total": 0,
        "date": date_filter or date.today().isoformat(),
        "employee_total": _active_employee_total(db),
        "attendance_data_available": False,
        "source": "attendance-not-configured",
        "message": "真实考勤域尚未接入，未返回合成考勤数据",
    }


@router.get("/attendance")
def list_attendance(
    date_filter: Optional[str] = Query(None, alias="date", description="日期筛选"),
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """Return department attendance statistics for the admin attendance page."""

    return _empty_attendance_payload(db, date_filter)


@router.get("/attendance/statistics")
def get_attendance_statistics(
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    return {
        "total": 0,
        "present": 0,
        "leave": 0,
        "late": 0,
        "earlyLeave": 0,
        "absence": 0,
        "attendanceRate": 0.0,
        "departments": [],
        "employee_total": _active_employee_total(db),
        "attendance_data_available": False,
        "source": "attendance-not-configured",
    }


@router.get("/attendance/my-records")
def get_my_attendance_records(
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    return {
        "items": [],
        "total": 0,
        "attendance_data_available": False,
        "source": "attendance-not-configured",
    }


@router.get("/attendance/export")
def export_attendance(
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_active_user),
) -> Response:
    output = StringIO()
    output.write("department,total,present,leave,late,earlyLeave,absence,attendanceRate\n")
    filename = f"attendance-{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/attendance/clock-in")
def clock_in(
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="真实考勤打卡尚未接入，未写入打卡记录",
    )


@router.post("/attendance/clock-out")
def clock_out(
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="真实考勤签退尚未接入，未写入签退记录",
    )


@router.get("/attendance/{record_id}")
def get_attendance_record(
    record_id: str,
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"真实考勤记录尚未接入，未找到记录 {record_id}",
    )
