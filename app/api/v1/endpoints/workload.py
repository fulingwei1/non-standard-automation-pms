# -*- coding: utf-8 -*-
"""
资源排程与负荷管理 API endpoints
包含：工程师负荷统计、团队负荷统计、负荷看板、负荷热力图、可用资源查询
"""
from typing import Any, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, extract

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.organization import Employee, Department
from app.models.project import Project
from app.models.progress import Task
from app.models.pmo import PmoResourceAllocation
from app.schemas.workload import (
    UserWorkloadResponse, UserWorkloadSummary, ProjectWorkloadItem,
    DailyWorkloadItem, TaskWorkloadItem,
    TeamWorkloadResponse, TeamWorkloadItem,
    WorkloadHeatmapResponse,
    AvailableResourceResponse, AvailableResourceItem,
    WorkloadDashboardResponse, WorkloadDashboardSummary
)
from app.schemas.common import ResponseModel

router = APIRouter()


# 标准工时：每月176小时（22天 × 8小时）
STANDARD_MONTHLY_HOURS = 176.0


def calculate_workdays(start_date: date, end_date: date) -> int:
    """计算工作日数量（简单实现，不考虑节假日）"""
    days = (end_date - start_date).days + 1
    # 简单计算：每周5个工作日
    weeks = days // 7
    workdays = weeks * 5 + min(days % 7, 5)
    return workdays


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
    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        # 计算当月最后一天
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
    
    # 计算标准工时（基于日期范围）
    workdays = calculate_workdays(start_date, end_date)
    standard_hours = workdays * 8.0  # 每天8小时
    
    # 1. 统计任务分配工时（从Task表）
    tasks = db.query(Task).filter(
        Task.owner_id == user_id,
        Task.plan_start <= end_date,
        Task.plan_end >= start_date,
        Task.status != 'CANCELLED'
    ).all()
    
    # 计算分配工时（基于plan_days）
    total_assigned_hours = 0.0
    task_list = []
    for task in tasks:
        # 使用plan_days * 8计算工时
        if task.plan_start and task.plan_end:
            days = (task.plan_end - task.plan_start).days + 1
            hours = days * 8.0
        else:
            hours = 0.0
        
        total_assigned_hours += hours
        
        task_list.append(TaskWorkloadItem(
            task_id=task.id,
            task_name=task.task_name,
            project_code=task.project.project_code if task.project else None,
            plan_hours=hours,
            actual_hours=0.0,  # Task模型没有actual_hours字段，需要从ProgressLog统计
            progress=task.progress_percent or 0,
            deadline=task.plan_end
        ))
    
    # 2. 统计资源分配工时（从PmoResourceAllocation表）
    allocations = db.query(PmoResourceAllocation).filter(
        PmoResourceAllocation.resource_id == user_id,
        PmoResourceAllocation.start_date <= end_date,
        PmoResourceAllocation.end_date >= start_date,
        PmoResourceAllocation.status != 'CANCELLED'
    ).all()
    
    for alloc in allocations:
        if alloc.planned_hours:
            total_assigned_hours += float(alloc.planned_hours)
    
    # 3. 计算实际工时（从PmoResourceAllocation的actual_hours）
    total_actual_hours = 0.0
    # Task模型没有actual_hours字段，实际工时需要从ProgressLog或其他表统计
    # 这里暂时只统计资源分配的实际工时
    
    for alloc in allocations:
        if alloc.actual_hours:
            total_actual_hours += float(alloc.actual_hours)
    
    # 4. 按项目统计
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
        
        if task.plan_start and task.plan_end:
            days = (task.plan_end - task.plan_start).days + 1
            hours = days * 8.0
        else:
            hours = 0.0
        
        project_dict[project.id]['assigned_hours'] += hours
        project_dict[project.id]['actual_hours'] += 0.0  # Task模型没有actual_hours字段
        project_dict[project.id]['task_count'] += 1
    
    project_list = [ProjectWorkloadItem(**p) for p in project_dict.values()]
    
    # 5. 计算分配率和效率
    allocation_rate = (total_assigned_hours / standard_hours * 100) if standard_hours > 0 else 0.0
    efficiency = (total_actual_hours / total_assigned_hours * 100) if total_assigned_hours > 0 else 0.0
    
    # 6. 每日负荷（简化实现，按周统计）
    daily_load = []
    current = start_date
    while current <= end_date:
        # 计算该日的分配工时和实际工时
        day_assigned = 0.0
        day_actual = 0.0
        
        for task in tasks:
            if task.plan_start <= current <= task.plan_end:
                if task.estimated_hours:
                    day_assigned += float(task.estimated_hours) / max((task.plan_end - task.plan_start).days + 1, 1)
                else:
                    day_assigned += 8.0  # 默认每天8小时
        
        daily_load.append(DailyWorkloadItem(
            date=current,
            assigned=round(day_assigned, 2),
            actual=round(day_actual, 2)
        ))
        current += timedelta(days=1)
    
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
        
        # 获取用户角色（从Employee表或User表）
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
    
    available_resources = []
    
    for user in users:
        # 计算分配工时
        tasks = db.query(Task).filter(
            Task.owner_id == user.id,
            Task.plan_start <= end_date,
            Task.plan_end >= start_date,
            Task.status != 'CANCELLED'
        ).all()
        
        assigned_hours = 0.0
        for task in tasks:
            if task.plan_start and task.plan_end:
                days = (task.plan_end - task.plan_start).days + 1
                hours = days * 8.0
            else:
                hours = 0.0
            assigned_hours += hours
        
        allocations = db.query(PmoResourceAllocation).filter(
            PmoResourceAllocation.resource_id == user.id,
            PmoResourceAllocation.start_date <= end_date,
            PmoResourceAllocation.end_date >= start_date,
            PmoResourceAllocation.status != 'CANCELLED'
        ).all()
        
        for alloc in allocations:
            if alloc.planned_hours:
                assigned_hours += float(alloc.planned_hours)
        
        # 计算可用工时
        available_hours = max(0, standard_hours - assigned_hours)
        
        # 只返回可用工时大于等于min_hours的用户
        if available_hours >= min_hours:
            # 获取技能（简化实现，从WorkerSkill表或User表）
            skills = []
            # TODO: 从WorkerSkill表获取技能
            
            role = None
            if hasattr(user, 'position'):
                role = user.position
            
            available_resources.append(AvailableResourceItem(
                user_id=user.id,
                user_name=user.real_name or user.username,
                dept_name=user.department,
                role=role,
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

