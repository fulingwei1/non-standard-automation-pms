# -*- coding: utf-8 -*-
"""
资源负荷管理 - 辅助工具函数
"""

from datetime import date, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.models.pmo import PmoResourceAllocation
from app.models.progress import Task
from app.models.user import User


# 标准工时：每月176小时（22天 × 8小时）
STANDARD_MONTHLY_HOURS = 176.0


def calculate_workdays(start_date: date, end_date: date) -> int:
    """计算工作日数量（简单实现，不考虑节假日）"""
    days = (end_date - start_date).days + 1
    # 简单计算：每周5个工作日
    weeks = days // 7
    workdays = weeks * 5 + min(days % 7, 5)
    return workdays


def get_default_date_range() -> tuple:
    """获取默认日期范围（当前月）"""
    today = date.today()
    start = date(today.year, today.month, 1)
    if today.month == 12:
        end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(today.year, today.month + 1, 1) - timedelta(days=1)
    return start, end


def calculate_user_assigned_hours(db: Session, user_id: int, start_date: date, end_date: date) -> float:
    """计算用户在指定时间范围内的已分配工时"""
    assigned_hours = 0.0

    # 从任务计算工时
    tasks = db.query(Task).filter(
        Task.owner_id == user_id,
        Task.plan_start <= end_date,
        Task.plan_end >= start_date,
        Task.status != 'CANCELLED'
    ).all()

    for task in tasks:
        if task.plan_start and task.plan_end:
            days = (task.plan_end - task.plan_start).days + 1
            assigned_hours += days * 8.0

    # 从PMO资源分配计算工时
    allocations = db.query(PmoResourceAllocation).filter(
        PmoResourceAllocation.resource_id == user_id,
        PmoResourceAllocation.start_date <= end_date,
        PmoResourceAllocation.end_date >= start_date,
        PmoResourceAllocation.status != 'CANCELLED'
    ).all()

    for alloc in allocations:
        if alloc.planned_hours:
            assigned_hours += float(alloc.planned_hours)

    return assigned_hours


def get_user_skills_list(db: Session, user: User) -> List[str]:
    """获取用户的技能名称列表（用于轻量展示/筛选）"""
    skills: List[str] = []
    try:
        from app.models.production import ProcessDict, Worker, WorkerSkill

        worker = db.query(Worker).filter(
            Worker.user_id == user.id,
            Worker.is_active == True
        ).first()

        if worker:
            worker_skills = db.query(WorkerSkill).filter(
                WorkerSkill.worker_id == worker.id
            ).all()

            for ws in worker_skills:
                process = db.query(ProcessDict).filter(
                    ProcessDict.id == ws.process_id
                ).first()

                if process:
                    if process.process_name:
                        skills.append(process.process_name)
        else:
            # 从用户职位推断技能
            if user.position:
                skills.append(user.position)
            if user.department:
                skills.append(f"{user.department}通用技能")
    except Exception:
        if user.position:
            skills.append(user.position)
    return skills
