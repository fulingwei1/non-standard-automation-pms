# -*- coding: utf-8 -*-
"""资源负荷看板兼容接口。"""

from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Department
from app.models.progress import Task
from app.models.timesheet import Timesheet
from app.models.user import User

router = APIRouter(tags=["workload-compat"])


def _coerce_dept_id(dept_id: Optional[str]) -> Optional[int]:
    if not dept_id or dept_id == "all":
        return None
    try:
        return int(dept_id)
    except (TypeError, ValueError):
        return None


def _normalize_period(start_date: Optional[date], end_date: Optional[date]) -> tuple[date, date]:
    today = date.today()
    start = start_date or date(today.year, today.month, 1)
    end = end_date or today
    if end < start:
        return end, start
    return start, end


def _workdays(start: date, end: date) -> int:
    days = (end - start).days + 1
    return sum(1 for i in range(days) if (start + timedelta(days=i)).weekday() < 5)


def _task_hours_in_period(task: Task, start: date, end: date) -> float:
    if task.plan_start and task.plan_end:
        overlap_start = max(task.plan_start, start)
        overlap_end = min(task.plan_end, end)
        if overlap_end < overlap_start:
            return 0.0
        return float(_workdays(overlap_start, overlap_end) * 8)
    return 8.0


def _build_team_workload(
    db: Session,
    *,
    dept_id: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
) -> list[dict[str, Any]]:
    start, end = _normalize_period(start_date, end_date)
    normalized_dept_id = _coerce_dept_id(dept_id)

    users_query = db.query(User).filter(User.is_active == True)
    if normalized_dept_id is not None:
        users_query = users_query.filter(User.department_id == normalized_dept_id)
    users = users_query.order_by(User.id.asc()).limit(500).all()
    user_ids = [user.id for user in users]
    if not user_ids:
        return []

    department_names = {
        dept.id: dept.dept_name
        for dept in db.query(Department).filter(Department.id.in_({u.department_id for u in users if u.department_id})).all()
    }

    actual_hours = defaultdict(float)
    actual_rows = (
        db.query(Timesheet.user_id, func.sum(Timesheet.hours))
        .filter(
            Timesheet.user_id.in_(user_ids),
            Timesheet.work_date >= start,
            Timesheet.work_date <= end,
        )
        .group_by(Timesheet.user_id)
        .all()
    )
    for user_id, hours in actual_rows:
        actual_hours[user_id] = float(hours or 0)

    task_query = db.query(Task).filter(
        Task.owner_id.in_(user_ids),
        Task.status != "CANCELLED",
        or_(Task.plan_start.is_(None), Task.plan_start <= end),
        or_(Task.plan_end.is_(None), Task.plan_end >= start),
    )
    task_rows = task_query.all()

    assigned_hours = defaultdict(float)
    task_count = defaultdict(int)
    overdue_count = defaultdict(int)
    today = date.today()
    for task in task_rows:
        if task.owner_id is None:
            continue
        assigned_hours[task.owner_id] += _task_hours_in_period(task, start, end)
        task_count[task.owner_id] += 1
        if task.plan_end and task.plan_end < today and task.status not in ("DONE", "COMPLETED"):
            overdue_count[task.owner_id] += 1

    standard_hours = float(_workdays(start, end) * 8)
    items = []
    for user in users:
        assigned = round(assigned_hours[user.id], 2)
        actual = round(actual_hours[user.id], 2)
        effective_assigned = assigned if assigned > 0 else actual
        allocation_rate = (
            round(effective_assigned / standard_hours * 100, 2) if standard_hours else 0.0
        )
        items.append(
            {
                "user_id": user.id,
                "user_name": user.real_name or user.username,
                "dept_name": user.department or department_names.get(user.department_id),
                "role": user.position,
                "assigned_hours": effective_assigned,
                "standard_hours": standard_hours,
                "actual_hours": actual,
                "allocation_rate": allocation_rate,
                "task_count": task_count[user.id],
                "overdue_count": overdue_count[user.id],
            }
        )

    return items


def _summary_for_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    total_users = len(items)
    avg_allocation = (
        round(sum(item["allocation_rate"] for item in items) / total_users, 2)
        if total_users
        else 0.0
    )
    overload_count = sum(1 for item in items if item["allocation_rate"] >= 120)
    idle_count = sum(1 for item in items if item["allocation_rate"] < 80)
    normal_users = max(total_users - overload_count - idle_count, 0)
    total_assigned_hours = round(sum(item["assigned_hours"] for item in items), 2)
    total_actual_hours = round(sum(item["actual_hours"] for item in items), 2)

    return {
        "total_users": total_users,
        "avg_allocation_rate": avg_allocation,
        "average_allocation_rate": avg_allocation,
        "overload_count": overload_count,
        "overloaded_users": overload_count,
        "idle_count": idle_count,
        "underloaded_users": idle_count,
        "normal_users": normal_users,
        "total_assigned_hours": total_assigned_hours,
        "total_actual_hours": total_actual_hours,
    }


@router.get("/team", status_code=status.HTTP_200_OK)
def get_team_workload(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: Optional[str] = Query(None, description="部门ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """团队负荷列表，供 `/workload-board` 使用。"""
    return {
        "items": _build_team_workload(
            db,
            dept_id=dept_id,
            start_date=start_date,
            end_date=end_date,
        )
    }


@router.get("/dashboard", status_code=status.HTTP_200_OK)
def get_workload_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: Optional[str] = Query(None, description="部门ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """资源负荷汇总，供旧 `/workload/dashboard` 前端契约使用。"""
    items = _build_team_workload(
        db,
        dept_id=dept_id,
        start_date=start_date,
        end_date=end_date,
    )
    return {"summary": _summary_for_items(items), "team_workload": items}
