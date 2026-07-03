# -*- coding: utf-8 -*-
"""Administrative attendance compatibility routes.

The current attendance page consumes department-level attendance statistics from
``/admin/attendance``.  The project does not yet have a full attendance domain
model, so these routes derive stable demo statistics from active employees and
fall back to representative departments when the database is sparse.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from io import StringIO
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api import deps
from app.models.organization import Employee
from app.models.user import User

router = APIRouter()


FALLBACK_DEPARTMENTS = [
    ("销售部", 12),
    ("项目管理部", 8),
    ("机械设计部", 10),
    ("电气软件部", 11),
    ("生产装配部", 16),
    ("质量部", 6),
    ("采购仓储部", 7),
    ("综合管理部", 5),
]


def _safe_department(value: Optional[str]) -> str:
    name = (value or "").strip()
    return name or "未分配"


def _active_department_counts(db: Session) -> Counter[str]:
    counts: Counter[str] = Counter()

    employees = (
        db.query(Employee.department)
        .filter(Employee.is_active.is_(True))
        .all()
    )
    for (department,) in employees:
        counts[_safe_department(department)] += 1

    users = (
        db.query(User.department)
        .filter(User.is_active.is_(True))
        .all()
    )
    for (department,) in users:
        counts.setdefault(_safe_department(department), 0)

    return counts


def _build_department_stat(department: str, total: int, index: int) -> Dict[str, Any]:
    total = max(int(total or 0), 0)
    if total == 0:
        return {
            "department": department,
            "total": 0,
            "present": 0,
            "leave": 0,
            "late": 0,
            "earlyLeave": 0,
            "absence": 0,
            "attendanceRate": 0.0,
        }

    leave = 1 if total >= 6 and index % 3 == 0 else 0
    late = 1 if total >= 5 and index % 2 == 1 else 0
    early_leave = 1 if total >= 9 and index % 4 == 2 else 0
    absence = 1 if total >= 12 and index % 5 == 3 else 0
    present = max(total - leave - absence, 0)
    attendance_rate = round((present / total) * 100, 1) if total else 0.0

    return {
        "department": department,
        "total": total,
        "present": present,
        "leave": leave,
        "late": late,
        "earlyLeave": early_leave,
        "absence": absence,
        "attendanceRate": attendance_rate,
    }


def _department_stats(db: Session) -> List[Dict[str, Any]]:
    counts = _active_department_counts(db)
    if sum(counts.values()) < 8 or len(counts) < 3:
        counts.update(dict(FALLBACK_DEPARTMENTS))

    sorted_items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [
        _build_department_stat(department, total, index)
        for index, (department, total) in enumerate(sorted_items)
    ]


@router.get("/attendance")
def list_attendance(
    date_filter: Optional[str] = Query(None, alias="date", description="日期筛选"),
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """Return department attendance statistics for the admin attendance page."""

    items = _department_stats(db)
    return {
        "items": items,
        "total": len(items),
        "date": date_filter or date.today().isoformat(),
        "source": "employee-demo",
    }


@router.get("/attendance/statistics")
def get_attendance_statistics(
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    items = _department_stats(db)
    total = sum(item["total"] for item in items)
    present = sum(item["present"] for item in items)
    leave = sum(item["leave"] for item in items)
    late = sum(item["late"] for item in items)
    early_leave = sum(item["earlyLeave"] for item in items)
    absence = sum(item["absence"] for item in items)
    return {
        "total": total,
        "present": present,
        "leave": leave,
        "late": late,
        "earlyLeave": early_leave,
        "absence": absence,
        "attendanceRate": round((present / total) * 100, 1) if total else 0.0,
        "departments": items,
    }


@router.get("/attendance/my-records")
def get_my_attendance_records(
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    today = date.today().isoformat()
    return {
        "items": [
            {
                "id": f"my-{today}",
                "date": today,
                "clockIn": "08:27",
                "clockOut": "18:04",
                "status": "normal",
                "workHours": 8.5,
            }
        ],
        "total": 1,
    }


@router.get("/attendance/export")
def export_attendance(
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_active_user),
) -> Response:
    output = StringIO()
    output.write("department,total,present,leave,late,earlyLeave,absence,attendanceRate\n")
    for item in _department_stats(db):
        output.write(
            "{department},{total},{present},{leave},{late},{earlyLeave},{absence},{attendanceRate}\n".format(
                **item
            )
        )
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
    return {"success": True, "message": "打卡成功", "clockIn": datetime.now().strftime("%H:%M")}


@router.post("/attendance/clock-out")
def clock_out(
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    return {"success": True, "message": "签退成功", "clockOut": datetime.now().strftime("%H:%M")}


@router.get("/attendance/{record_id}")
def get_attendance_record(
    record_id: str,
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    today = date.today().isoformat()
    return {
        "id": record_id,
        "date": today,
        "employee": "当前用户",
        "department": "综合管理部",
        "clockIn": "08:27",
        "clockOut": "18:04",
        "status": "normal",
        "workHours": 8.5,
    }
