# -*- coding: utf-8 -*-
"""
用户负荷统计服务
"""

from datetime import date, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.models.pmo import PmoResourceAllocation
from app.models.progress import Task
from app.schemas.workload import (
    DailyWorkloadItem,
    ProjectWorkloadItem,
    TaskWorkloadItem,
)


def calculate_workdays(start_date: date, end_date: date) -> int:
    """
    计算工作日数量（简单实现，不考虑节假日）

    Returns:
        int: 工作日数量
    """
    days = (end_date - start_date).days + 1
    weeks = days // 7
    workdays = weeks * 5 + min(days % 7, 5)
    return workdays


def get_user_tasks(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date
) -> List[Task]:
    """
    获取用户的任务列表

    Returns:
        List[Task]: 任务列表
    """
    return db.query(Task).filter(
        Task.owner_id == user_id,
        Task.plan_start <= end_date,
        Task.plan_end >= start_date,
        Task.status != 'CANCELLED'
    ).all()


def get_user_allocations(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date
) -> List[PmoResourceAllocation]:
    """
    获取用户的资源分配列表

    Returns:
        List[PmoResourceAllocation]: 资源分配列表
    """
    return db.query(PmoResourceAllocation).filter(
        PmoResourceAllocation.resource_id == user_id,
        PmoResourceAllocation.start_date <= end_date,
        PmoResourceAllocation.end_date >= start_date,
        PmoResourceAllocation.status != 'CANCELLED'
    ).all()


def calculate_task_hours(task: Task) -> float:
    """
    计算任务的分配工时

    Returns:
        float: 工时数
    """
    if task.plan_start and task.plan_end:
        days = (task.plan_end - task.plan_start).days + 1
        return days * 8.0
    return 0.0


def calculate_total_assigned_hours(
    tasks: List[Task],
    allocations: List[PmoResourceAllocation]
) -> float:
    """
    计算总分配工时

    Returns:
        float: 总分配工时
    """
    total = 0.0

    for task in tasks:
        total += calculate_task_hours(task)

    for alloc in allocations:
        if alloc.planned_hours:
            total += float(alloc.planned_hours)

    return total


def calculate_total_actual_hours(allocations: List[PmoResourceAllocation]) -> float:
    """
    计算总实际工时

    Returns:
        float: 总实际工时
    """
    return sum([float(alloc.actual_hours) for alloc in allocations if alloc.actual_hours])


def build_project_workload(tasks: List[Task]) -> List[ProjectWorkloadItem]:
    """
    构建项目负荷列表

    Returns:
        List[ProjectWorkloadItem]: 项目负荷列表
    """
    project_dict = {}

    for task in tasks:
        if not task.project_id:
            continue

        project = task.project
        if project.id not in project_dict:
            project_dict[project.id] = {
                'project_id': project.id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'assigned_hours': 0.0,
                'actual_hours': 0.0,
                'task_count': 0
            }

        hours = calculate_task_hours(task)
        project_dict[project.id]['assigned_hours'] += hours
        project_dict[project.id]['task_count'] += 1

    return [ProjectWorkloadItem(**p) for p in project_dict.values()]


def build_task_list(tasks: List[Task]) -> List[TaskWorkloadItem]:
    """
    构建任务列表

    Returns:
        List[TaskWorkloadItem]: 任务列表
    """
    return [
        TaskWorkloadItem(
            task_id=task.id,
            task_name=task.task_name,
            project_code=task.project.project_code if task.project else None,
            plan_hours=calculate_task_hours(task),
            actual_hours=0.0,
            progress=task.progress_percent or 0,
            deadline=task.plan_end
        )
        for task in tasks
    ]


def build_daily_load(
    tasks: List[Task],
    start_date: date,
    end_date: date
) -> List[DailyWorkloadItem]:
    """
    构建每日负荷列表

    Returns:
        List[DailyWorkloadItem]: 每日负荷列表
    """
    daily_load = []
    current = start_date

    while current <= end_date:
        day_assigned = 0.0
        day_actual = 0.0

        for task in tasks:
            if task.plan_start <= current <= task.plan_end:
                if task.estimated_hours:
                    days = (task.plan_end - task.plan_start).days + 1
                    day_assigned += float(task.estimated_hours) / max(days, 1)
                else:
                    day_assigned += 8.0

        daily_load.append(DailyWorkloadItem(
            date=current,
            assigned=round(day_assigned, 2),
            actual=round(day_actual, 2)
        ))
        current += timedelta(days=1)

    return daily_load
