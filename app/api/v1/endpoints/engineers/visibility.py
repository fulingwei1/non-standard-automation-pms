# -*- coding: utf-8 -*-
"""
工程师进度可视化 API 端点
包含：跨部门进度视图
"""

import logging
from collections import defaultdict
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectMember, ProjectStage
from app.models.task_center import TaskUnified
from app.models.user import User
from app.schemas import engineer as schemas

logger = logging.getLogger(__name__)

router = APIRouter()


def _collect_department_stats(db: Session, all_tasks, User):
    """收集部门统计信息"""
    dept_stats = defaultdict(lambda: {
        'department_id': 0,
        'department_name': '',
        'total_tasks': 0,
        'completed_tasks': 0,
        'in_progress_tasks': 0,
        'delayed_tasks': 0,
        'members': defaultdict(lambda: {'name': '', 'total_tasks': 0, 'completed': 0, 'in_progress': 0})
    })

    for task in all_tasks:
        if task.assignee_id:
            user = db.query(User).filter(User.id == task.assignee_id).first()
            if user and user.department:
                dept_name = user.department
                dept_stats[dept_name]['department_name'] = dept_name
                dept_stats[dept_name]['total_tasks'] += 1

                if task.status == 'COMPLETED':
                    dept_stats[dept_name]['completed_tasks'] += 1
                elif task.status == 'IN_PROGRESS':
                    dept_stats[dept_name]['in_progress_tasks'] += 1

                if task.is_delayed:
                    dept_stats[dept_name]['delayed_tasks'] += 1

                member_key = user.real_name or user.username
                dept_stats[dept_name]['members'][member_key]['name'] = member_key
                dept_stats[dept_name]['members'][member_key]['total_tasks'] += 1

                if task.status == 'COMPLETED':
                    dept_stats[dept_name]['members'][member_key]['completed'] += 1
                elif task.status == 'IN_PROGRESS':
                    dept_stats[dept_name]['members'][member_key]['in_progress'] += 1

    return dept_stats


def _build_department_progress(dept_stats, schemas):
    """构建部门进度响应"""
    department_progress = []
    assignee_progress_lookup = []

    for idx, (dept_name, stats) in enumerate(dept_stats.items(), 1):
        total = stats['total_tasks']
        completed = stats['completed_tasks']
        progress_pct = (completed / total * 100) if total > 0 else 0

        members = [
            schemas.MemberProgressSummary(
                name=m['name'],
                total_tasks=m['total_tasks'],
                completed_tasks=m['completed'],
                in_progress_tasks=m['in_progress'],
                progress_pct=(m['completed'] / m['total_tasks'] * 100) if m['total_tasks'] > 0 else 0
            )
            for m in stats['members'].values()
        ]

        department_progress.append(schemas.DepartmentProgressSummary(
            department_id=idx,
            department_name=dept_name,
            total_tasks=stats['total_tasks'],
            completed_tasks=stats['completed_tasks'],
            in_progress_tasks=stats['in_progress_tasks'],
            delayed_tasks=stats['delayed_tasks'],
            progress_pct=round(progress_pct, 2),
            members=members
        ))
        assignee_progress_lookup.extend(members)

    return department_progress, assignee_progress_lookup


def _build_active_delays(db: Session, delayed_tasks, User, schemas):
    """构建活跃延期列表"""
    active_delays = []
    for task in delayed_tasks:
        user = db.query(User).filter(User.id == task.assignee_id).first()
        delay_days = 0
        if task.deadline and task.new_completion_date:
            delay_days = (task.new_completion_date - task.deadline.date()).days

        active_delays.append(schemas.ActiveDelayInfo(
            task_id=task.id,
            task_title=task.title,
            assignee_name=user.real_name if user else "未知",
            department=user.department if user else "未知",
            delay_days=delay_days,
            impact_scope=task.delay_impact_scope or "LOCAL",
            new_completion_date=task.new_completion_date or date.today(),
            delay_reason=task.delay_reason or "",
            reported_at=task.delay_reported_at or datetime.now()
        ))
    return active_delays


@router.get("/projects/{project_id}/progress-visibility", response_model=schemas.ProjectProgressVisibilityResponse)
def get_project_progress_visibility(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    获取项目的跨部门进度视图
    解决痛点：各部门可以看到彼此的工作进度
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 验证权限（项目成员可查看）
    is_member = db.query(ProjectMember).filter(
        and_(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
            ProjectMember.is_active
        )
    ).first()

    if not is_member and project.pm_id != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限查看此项目进度")

    # 获取项目所有任务
    all_tasks = db.query(TaskUnified).filter(TaskUnified.project_id == project_id).all()

    # 收集部门统计并构建进度响应
    dept_stats = _collect_department_stats(db, all_tasks, User)
    department_progress, assignee_progress_lookup = _build_department_progress(dept_stats, schemas)

    # 阶段进度统计
    stages = db.query(ProjectStage).filter(ProjectStage.project_id == project_id).all()
    stage_progress = {
        stage.stage_code: schemas.StageProgressSummary(
            progress=float(stage.progress_pct) if stage.progress_pct else 0.0,
            status=stage.status
        )
        for stage in stages
    }

    # 活跃延期列表
    delayed_tasks = [t for t in all_tasks if t.is_delayed and t.status not in ['COMPLETED', 'CANCELLED']]
    active_delays = _build_active_delays(db, delayed_tasks, User, schemas)

    # 整体进度
    overall_progress = float(project.progress_pct) if project.progress_pct else 0.0

    return schemas.ProjectProgressVisibilityResponse(
        project_id=project.id,
        project_name=project.project_name,
        overall_progress=overall_progress,
        department_progress=department_progress,
        stage_progress=stage_progress,
        assignee_progress=assignee_progress_lookup,
        active_delays=active_delays,
        last_updated_at=datetime.now()
    )
