# -*- coding: utf-8 -*-
"""
用户负荷端点

包含工程师负荷详情查询
"""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Department
from app.models.user import User
from app.schemas.workload import (
    UserWorkloadResponse,
    UserWorkloadSummary,
)

from .utils import calculate_workdays

router = APIRouter()


@router.get("/workload/user/{user_id}", response_model=UserWorkloadResponse)
def get_user_workload(
    user_id: int,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工程师负荷详情

    - **user_id**: 用户ID
    - **start_date**: 开始日期（默认：当前月第一天）
    - **end_date**: 结束日期（默认：当前月最后一天）
    """
    from app.services.user_workload_service import (
        build_daily_load,
        build_project_workload,
        build_task_list,
        calculate_total_actual_hours,
        calculate_total_assigned_hours,
        calculate_workdays,
        get_user_allocations,
        get_user_tasks,
    )

    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    # 获取用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取部门信息
    dept_name = None
    if user.department:
        dept = db.query(Department).filter(Department.name == user.department).first()
        if dept:
            dept_name = dept.name

    # 计算标准工时
    workdays = calculate_workdays(start_date, end_date)
    standard_hours = workdays * 8.0

    # 获取任务和资源分配
    tasks = get_user_tasks(db, user_id, start_date, end_date)
    allocations = get_user_allocations(db, user_id, start_date, end_date)

    # 计算工时
    total_assigned_hours = calculate_total_assigned_hours(tasks, allocations)
    total_actual_hours = calculate_total_actual_hours(allocations)

    # 构建数据
    project_list = build_project_workload(tasks)
    task_list = build_task_list(tasks)
    daily_load = build_daily_load(tasks, start_date, end_date)

    # 计算分配率和效率
    allocation_rate = (total_assigned_hours / standard_hours * 100) if standard_hours > 0 else 0.0
    efficiency = (total_actual_hours / total_assigned_hours * 100) if total_assigned_hours > 0 else 0.0

    return UserWorkloadResponse(
        user_id=user.id,
        user_name=user.real_name or user.username,
        dept_name=dept_name,
        period={"start": str(start_date), "end": str(end_date)},
        summary=UserWorkloadSummary(
            total_assigned_hours=round(total_assigned_hours, 2),
            standard_hours=round(standard_hours, 2),
            allocation_rate=round(allocation_rate, 2),
            actual_hours=round(total_actual_hours, 2),
            efficiency=round(efficiency, 2)
        ),
        by_project=project_list,
        daily_load=daily_load,
        tasks=task_list
    )
