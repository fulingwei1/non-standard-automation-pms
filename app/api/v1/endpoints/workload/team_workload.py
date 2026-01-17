# -*- coding: utf-8 -*-
"""
团队负荷端点

包含团队负荷概览、资源负荷看板
"""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Department
from app.models.pmo import PmoResourceAllocation
from app.models.progress import Task
from app.models.user import User
from app.schemas.workload import (
    TeamWorkloadItem,
    TeamWorkloadResponse,
    WorkloadDashboardResponse,
    WorkloadDashboardSummary,
)

from .utils import calculate_workdays

router = APIRouter()


@router.get("/workload/team", response_model=TeamWorkloadResponse)
def get_team_workload(
    db: Session = Depends(deps.get_db),
    dept_id: Optional[int] = Query(None, description="部门ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取团队负荷概览

    - **dept_id**: 部门ID筛选
    - **project_id**: 项目ID筛选
    - **start_date**: 开始日期
    - **end_date**: 结束日期
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

    # 获取用户列表
    query_users = db.query(User).filter(User.is_active == True)

    if dept_id:
        dept = db.query(Department).filter(Department.id == dept_id).first()
        if dept:
            query_users = query_users.filter(User.department == dept.name)

    users = query_users.all()

    workdays = calculate_workdays(start_date, end_date)
    standard_hours = workdays * 8.0

    team_items = []
    for user in users:
        # 获取任务
        task_query = db.query(Task).filter(
            Task.owner_id == user.id,
            Task.plan_start <= end_date,
            Task.plan_end >= start_date,
            Task.status != 'CANCELLED'
        )

        if project_id:
            task_query = task_query.filter(Task.project_id == project_id)

        tasks = task_query.all()

        # 计算分配工时
        assigned_hours = 0.0
        task_count = len(tasks)
        overdue_count = 0

        for task in tasks:
            if task.plan_start and task.plan_end:
                days = (task.plan_end - task.plan_start).days + 1
                hours = days * 8.0
            else:
                hours = 0.0

            assigned_hours += hours

            # 检查是否逾期
            if task.plan_end and task.plan_end < today and task.status != 'DONE':
                overdue_count += 1

        # 获取资源分配
        alloc_query = db.query(PmoResourceAllocation).filter(
            PmoResourceAllocation.resource_id == user.id,
            PmoResourceAllocation.start_date <= end_date,
            PmoResourceAllocation.end_date >= start_date,
            PmoResourceAllocation.status != 'CANCELLED'
        )

        if project_id:
            alloc_query = alloc_query.filter(PmoResourceAllocation.project_id == project_id)

        allocations = alloc_query.all()

        for alloc in allocations:
            if alloc.planned_hours:
                assigned_hours += float(alloc.planned_hours)

        # 计算分配率
        allocation_rate = (assigned_hours / standard_hours * 100) if standard_hours > 0 else 0.0

        # 获取用户角色
        role = None
        if hasattr(user, 'position'):
            role = user.position

        team_items.append(TeamWorkloadItem(
            user_id=user.id,
            user_name=user.real_name or user.username,
            dept_name=user.department,
            role=role,
            assigned_hours=round(assigned_hours, 2),
            standard_hours=round(standard_hours, 2),
            allocation_rate=round(allocation_rate, 2),
            task_count=task_count,
            overdue_count=overdue_count
        ))

    return TeamWorkloadResponse(items=team_items)


@router.get("/workload/dashboard", response_model=WorkloadDashboardResponse)
def get_workload_dashboard(
    db: Session = Depends(deps.get_db),
    dept_id: Optional[int] = Query(None, description="部门ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    资源负荷看板

    - **dept_id**: 部门ID筛选
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    """
    # 获取团队负荷数据
    team_response = get_team_workload(
        db=db,
        dept_id=dept_id,
        project_id=None,
        start_date=start_date,
        end_date=end_date,
        current_user=current_user
    )

    team_items = team_response.items

    # 统计汇总
    total_users = len(team_items)
    overloaded_users = sum(1 for item in team_items if item.allocation_rate > 110)
    normal_users = sum(1 for item in team_items if 80 <= item.allocation_rate <= 110)
    underloaded_users = sum(1 for item in team_items if item.allocation_rate < 80)

    total_assigned = sum(item.assigned_hours for item in team_items)
    total_actual = 0.0  # 实际工时需要从任务中统计
    average_allocation = sum(item.allocation_rate for item in team_items) / total_users if total_users > 0 else 0.0

    return WorkloadDashboardResponse(
        summary=WorkloadDashboardSummary(
            total_users=total_users,
            overloaded_users=overloaded_users,
            normal_users=normal_users,
            underloaded_users=underloaded_users,
            total_assigned_hours=round(total_assigned, 2),
            total_actual_hours=round(total_actual, 2),
            average_allocation_rate=round(average_allocation, 2)
        ),
        team_workload=team_items
    )
