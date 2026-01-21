# -*- coding: utf-8 -*-
"""
项目工作量 CRUD 操作

路由: /projects/{project_id}/workload/
提供项目视角的工作量和资源管理
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.pmo import PmoResourceAllocation
from app.models.progress import Task
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.workload import TeamWorkloadItem, TeamWorkloadResponse
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


def _calculate_workdays(start_date: date, end_date: date) -> int:
    """计算工作日数量（排除周末）"""
    if start_date > end_date:
        return 0
    days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # 周一到周五
            days += 1
        current += timedelta(days=1)
    return days


@router.get("/team", response_model=TeamWorkloadResponse)
def get_project_team_workload(
    project_id: int = Path(..., description="项目ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目团队负荷"""
    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    # 获取项目相关的任务负责人
    task_owners = (
        db.query(Task.owner_id)
        .filter(Task.project_id == project_id, Task.owner_id.isnot(None))
        .distinct()
        .all()
    )
    owner_ids = [o[0] for o in task_owners]

    # 获取项目资源分配的人员
    alloc_resources = (
        db.query(PmoResourceAllocation.resource_id)
        .filter(
            PmoResourceAllocation.project_id == project_id,
            PmoResourceAllocation.resource_id.isnot(None),
        )
        .distinct()
        .all()
    )
    resource_ids = [r[0] for r in alloc_resources]

    # 合并去重
    user_ids = list(set(owner_ids + resource_ids))

    if not user_ids:
        return TeamWorkloadResponse(items=[])

    users = db.query(User).filter(User.id.in_(user_ids), User.is_active == True).all()

    workdays = _calculate_workdays(start_date, end_date)
    standard_hours = workdays * 8.0

    team_items = []
    for user in users:
        # 获取该用户在此项目的任务
        tasks = (
            db.query(Task)
            .filter(
                Task.owner_id == user.id,
                Task.project_id == project_id,
                Task.plan_start <= end_date,
                Task.plan_end >= start_date,
                Task.status != "CANCELLED",
            )
            .all()
        )

        # 计算分配工时
        assigned_hours = 0.0
        task_count = len(tasks)
        overdue_count = 0

        for task in tasks:
            if task.plan_start and task.plan_end:
                # 计算任务在时间范围内的天数
                task_start = max(task.plan_start, start_date)
                task_end = min(task.plan_end, end_date)
                if task_start <= task_end:
                    days = (task_end - task_start).days + 1
                    assigned_hours += days * 8.0

            # 检查是否逾期
            if task.plan_end and task.plan_end < today and task.status != "DONE":
                overdue_count += 1

        # 获取项目资源分配
        allocations = (
            db.query(PmoResourceAllocation)
            .filter(
                PmoResourceAllocation.resource_id == user.id,
                PmoResourceAllocation.project_id == project_id,
                PmoResourceAllocation.start_date <= end_date,
                PmoResourceAllocation.end_date >= start_date,
                PmoResourceAllocation.status != "CANCELLED",
            )
            .all()
        )

        for alloc in allocations:
            if alloc.planned_hours:
                assigned_hours += float(alloc.planned_hours)

        # 计算分配率
        allocation_rate = (
            (assigned_hours / standard_hours * 100) if standard_hours > 0 else 0.0
        )

        # 获取用户角色
        role = getattr(user, "position", None)

        team_items.append(
            TeamWorkloadItem(
                user_id=user.id,
                user_name=user.real_name or user.username,
                dept_name=user.department,
                role=role,
                assigned_hours=round(assigned_hours, 2),
                standard_hours=round(standard_hours, 2),
                allocation_rate=round(allocation_rate, 2),
                task_count=task_count,
                overdue_count=overdue_count,
            )
        )

    return TeamWorkloadResponse(items=team_items)


@router.get("/gantt", response_model=ResponseModel)
def get_project_workload_gantt(
    project_id: int = Path(..., description="项目ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目资源甘特图"""
    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    # 获取项目任务
    tasks = (
        db.query(Task)
        .filter(
            Task.project_id == project_id,
            Task.plan_start <= end_date,
            Task.plan_end >= start_date,
            Task.status != "CANCELLED",
        )
        .all()
    )

    # 按负责人分组
    user_tasks: Dict[int, List[Dict[str, Any]]] = {}
    user_cache: Dict[int, User] = {}

    for task in tasks:
        if not task.owner_id:
            continue

        if task.owner_id not in user_tasks:
            user_tasks[task.owner_id] = []
            user = db.query(User).filter(User.id == task.owner_id).first()
            if user:
                user_cache[task.owner_id] = user

        if task.plan_start and task.plan_end:
            user_tasks[task.owner_id].append(
                {
                    "task_id": task.id,
                    "task_name": task.task_name,
                    "start_date": task.plan_start.isoformat(),
                    "end_date": task.plan_end.isoformat(),
                    "progress": task.progress_percent or 0,
                    "status": task.status,
                }
            )

    # 构建甘特图数据
    gantt_data = []
    for user_id, tasks_list in user_tasks.items():
        user = user_cache.get(user_id)
        if user and tasks_list:
            gantt_data.append(
                {
                    "user_id": user_id,
                    "user_name": user.real_name or user.username,
                    "dept_name": user.department,
                    "tasks": tasks_list,
                }
            )

    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "project_name": project.project_name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "resources": gantt_data,
        },
    )


@router.get("/summary", response_model=ResponseModel)
def get_project_workload_summary(
    project_id: int = Path(..., description="项目ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目工作量汇总"""
    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    # 获取团队负荷数据
    team_response = get_project_team_workload(
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
        db=db,
        current_user=current_user,
    )

    team_items = team_response.items

    # 统计汇总
    total_users = len(team_items)
    overloaded_users = sum(1 for item in team_items if item.allocation_rate > 110)
    normal_users = sum(
        1 for item in team_items if 80 <= item.allocation_rate <= 110
    )
    underloaded_users = sum(1 for item in team_items if item.allocation_rate < 80)

    total_assigned = sum(item.assigned_hours for item in team_items)
    total_tasks = sum(item.task_count for item in team_items)
    total_overdue = sum(item.overdue_count for item in team_items)
    average_allocation = (
        sum(item.allocation_rate for item in team_items) / total_users
        if total_users > 0
        else 0.0
    )

    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "project_name": project.project_name,
            "total_team_members": total_users,
            "overloaded_users": overloaded_users,
            "normal_users": normal_users,
            "underloaded_users": underloaded_users,
            "total_assigned_hours": round(total_assigned, 2),
            "total_tasks": total_tasks,
            "overdue_tasks": total_overdue,
            "average_allocation_rate": round(average_allocation, 2),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    )
