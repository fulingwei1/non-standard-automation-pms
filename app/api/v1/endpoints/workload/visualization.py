# -*- coding: utf-8 -*-
"""
负荷可视化端点

包含热力图、甘特图、可用资源查询
"""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Department
from app.models.progress import Task
from app.models.user import User
from app.schemas.workload import (
    AvailableResourceItem,
    AvailableResourceResponse,
    WorkloadHeatmapResponse,
)

from .utils import calculate_user_assigned_hours, calculate_workdays, get_default_date_range, get_user_skills_list

router = APIRouter()


@router.get("/workload/heatmap", response_model=WorkloadHeatmapResponse)
def get_workload_heatmap(
    db: Session = Depends(deps.get_db),
    dept_id: Optional[int] = Query(None, description="部门ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期（默认：当前周）"),
    weeks: int = Query(4, ge=1, le=12, description="周数（1-12）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取负荷热力图数据

    - **dept_id**: 部门ID筛选
    - **start_date**: 开始日期（默认：当前周第一天）
    - **weeks**: 周数（默认4周）
    """
    # 默认使用当前周
    today = date.today()
    if not start_date:
        # 计算当前周的第一天（周一）
        days_since_monday = today.weekday()
        start_date = today - timedelta(days=days_since_monday)

    # 获取用户列表
    query_users = db.query(User).filter(User.is_active == True)

    if dept_id:
        dept = db.query(Department).filter(Department.id == dept_id).first()
        if dept:
            query_users = query_users.filter(User.department == dept.name)

    users = query_users.all()

    # 生成周列表
    week_labels = []
    current_week_start = start_date
    for i in range(weeks):
        week_labels.append(f"W{current_week_start.strftime('%U')}")
        current_week_start += timedelta(days=7)

    # 计算每个用户每周的负荷
    heatmap_data = []
    user_names = []

    for user in users:
        user_names.append(user.real_name or user.username)
        user_weekly_load = []

        current_week_start = start_date
        for week_idx in range(weeks):
            week_end = current_week_start + timedelta(days=6)

            # 计算该周的分配工时
            tasks = db.query(Task).filter(
                Task.owner_id == user.id,
                Task.plan_start <= week_end,
                Task.plan_end >= current_week_start,
                Task.status != 'CANCELLED'
            ).all()

            week_hours = 0.0
            for task in tasks:
                # 默认每天8小时
                task_start = max(task.plan_start, current_week_start) if task.plan_start else current_week_start
                task_end = min(task.plan_end, week_end) if task.plan_end else week_end
                if task_start <= task_end:
                    days_in_week = (task_end - task_start).days + 1
                    week_hours += days_in_week * 8.0

            # 计算分配率（基于标准工时40小时/周）
            allocation_rate = (week_hours / 40.0 * 100) if week_hours > 0 else 0.0
            user_weekly_load.append(round(allocation_rate, 1))

            current_week_start += timedelta(days=7)

        heatmap_data.append(user_weekly_load)

    return WorkloadHeatmapResponse(
        users=user_names,
        weeks=week_labels,
        data=heatmap_data
    )


@router.get("/workload/available", response_model=AvailableResourceResponse)
def get_available_resources(
    db: Session = Depends(deps.get_db),
    dept_id: Optional[int] = Query(None, description="部门ID筛选"),
    skill: Optional[str] = Query(None, description="技能筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    min_hours: float = Query(8.0, ge=0, description="最小可用工时"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    查询可用资源（负荷低于阈值的人员）

    - **dept_id**: 部门ID筛选
    - **skill**: 技能筛选
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **min_hours**: 最小可用工时（默认8小时）
    """
    # 使用默认日期范围
    if not start_date or not end_date:
        default_start, default_end = get_default_date_range()
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 获取用户列表
    query_users = db.query(User).filter(User.is_active == True)
    if dept_id:
        dept = db.query(Department).filter(Department.id == dept_id).first()
        if dept:
            query_users = query_users.filter(User.department == dept.name)

    users = query_users.all()
    workdays = calculate_workdays(start_date, end_date)
    standard_hours = workdays * 8.0
    available_resources = []

    for user in users:
        assigned_hours = calculate_user_assigned_hours(db, user.id, start_date, end_date)
        available_hours = max(0, standard_hours - assigned_hours)

        if available_hours >= min_hours:
            skills = get_user_skills_list(db, user)
            available_resources.append(AvailableResourceItem(
                user_id=user.id,
                user_name=user.real_name or user.username,
                dept_name=user.department,
                role=getattr(user, 'position', None),
                available_hours=round(available_hours, 2),
                skills=skills
            ))

    return AvailableResourceResponse(items=available_resources)


@router.get("/workload/gantt", response_model=dict)
def get_workload_gantt(
    db: Session = Depends(deps.get_db),
    dept_id: Optional[int] = Query(None, description="部门ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    资源甘特图数据

    返回资源在时间轴上的任务分配情况，用于可视化资源负荷
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

    # 构建甘特图数据
    gantt_data = []

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

        user_tasks = []
        for task in tasks:
            if task.plan_start and task.plan_end:
                user_tasks.append({
                    "task_id": task.id,
                    "task_name": task.task_name,
                    "project_id": task.project_id,
                    "project_code": task.project.code if hasattr(task, 'project') and task.project else None,
                    "start_date": task.plan_start.isoformat(),
                    "end_date": task.plan_end.isoformat(),
                    "progress": task.progress_percent or 0,
                    "status": task.status,
                })

        if user_tasks:
            gantt_data.append({
                "user_id": user.id,
                "user_name": user.real_name or user.username,
                "dept_name": user.department,
                "tasks": user_tasks
            })

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "resources": gantt_data
    }
