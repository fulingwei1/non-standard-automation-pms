# -*- coding: utf-8 -*-
"""
项目进度汇总与可视化

路由: /projects/{project_id}/progress/
提供项目视角的进度数据
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.progress import Task, TaskDependency
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.progress import (
    GanttDataResponse,
    GanttTaskItem,
    MachineProgressSummaryResponse,
    ProgressBoardColumn,
    ProgressBoardResponse,
    ProgressSummaryResponse,
)
from app.utils.permission_helpers import check_project_access_or_raise
from app.utils.db_helpers import get_or_404

router = APIRouter()


# ==================== 进度汇总 ====================


@router.get("/summary", response_model=ProgressSummaryResponse)
def get_project_progress_summary(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目进度汇总"""
    check_project_access_or_raise(db, current_user, project_id)

    project = get_or_404(db, Project, project_id, detail="项目不存在")

    # 获取所有任务
    tasks = db.query(Task).filter(Task.project_id == project_id).all()

    if not tasks:
        return ProgressSummaryResponse(
            project_id=project_id,
            project_name=project.project_name,
            overall_progress=0.0,
            stage_progress={},
            task_count=0,
            completed_count=0,
            in_progress_count=0,
            blocked_count=0,
            overdue_count=0,
        )

    # 计算整体进度（按权重加权平均）
    total_weight = sum(float(task.weight) for task in tasks)
    weighted_progress = sum(
        float(task.weight) * task.progress_percent for task in tasks
    )
    overall_progress = (weighted_progress / total_weight) if total_weight > 0 else 0.0

    # 按阶段统计进度
    stage_progress = {}
    for stage in ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]:
        stage_tasks = [t for t in tasks if t.stage == stage]
        if stage_tasks:
            stage_weight = sum(float(t.weight) for t in stage_tasks)
            stage_weighted = sum(float(t.weight) * t.progress_percent for t in stage_tasks)
            stage_progress[stage] = (
                (stage_weighted / stage_weight) if stage_weight > 0 else 0.0
            )

    # 统计任务状态
    task_count = len(tasks)
    completed_count = len([t for t in tasks if t.status == "DONE"])
    in_progress_count = len([t for t in tasks if t.status == "IN_PROGRESS"])
    blocked_count = len([t for t in tasks if t.status == "BLOCKED"])

    # 统计逾期任务
    today = date.today()
    overdue_count = len(
        [t for t in tasks if t.plan_end and t.plan_end < today and t.status != "DONE"]
    )

    # 计算延期天数（取最晚的逾期天数）
    delay_days = None
    if overdue_count > 0:
        max_delay = 0
        for task in tasks:
            if task.plan_end and task.plan_end < today and task.status != "DONE":
                delay = (today - task.plan_end).days
                max_delay = max(max_delay, delay)
        delay_days = max_delay if max_delay > 0 else None

    return ProgressSummaryResponse(
        project_id=project_id,
        project_name=project.project_name,
        overall_progress=round(overall_progress, 2),
        stage_progress=stage_progress,
        task_count=task_count,
        completed_count=completed_count,
        in_progress_count=in_progress_count,
        blocked_count=blocked_count,
        overdue_count=overdue_count,
        delay_days=delay_days,
    )


# ==================== 甘特图数据 ====================


@router.get("/gantt", response_model=GanttDataResponse)
def get_project_gantt_data(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目甘特图数据"""
    check_project_access_or_raise(db, current_user, project_id)

    project = get_or_404(db, Project, project_id, detail="项目不存在")

    # 获取所有任务
    tasks = db.query(Task).filter(Task.project_id == project_id).all()

    # 获取所有依赖关系
    task_ids = [t.id for t in tasks]
    dependencies = (
        db.query(TaskDependency).filter(TaskDependency.task_id.in_(task_ids)).all()
    )
    dep_map = {}  # task_id -> [depends_on_task_ids]
    for dep in dependencies:
        if dep.task_id not in dep_map:
            dep_map[dep.task_id] = []
        dep_map[dep.task_id].append(dep.depends_on_task_id)

    # 构建甘特图任务项
    gantt_tasks = []
    for task in tasks:
        # 获取负责人名称
        owner_name = None
        if task.owner_id:
            owner = db.query(User).filter(User.id == task.owner_id).first()
            owner_name = owner.real_name or owner.username if owner else None

        gantt_task = GanttTaskItem(
            id=task.id,
            name=task.task_name,
            start=task.plan_start or date.today(),
            end=task.plan_end or date.today(),
            progress=task.progress_percent,
            status=task.status,
            dependencies=dep_map.get(task.id, []),
            owner=owner_name,
        )
        gantt_tasks.append(gantt_task)

    return GanttDataResponse(
        project_id=project_id, project_name=project.project_name, tasks=gantt_tasks
    )


# ==================== 进度看板 ====================


@router.get("/board", response_model=ProgressBoardResponse)
def get_project_progress_board(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目进度看板数据"""
    check_project_access_or_raise(db, current_user, project_id)

    project = get_or_404(db, Project, project_id, detail="项目不存在")

    # 获取所有任务
    tasks = db.query(Task).filter(Task.project_id == project_id).all()

    # 按状态分组
    status_groups = {
        "TODO": [],
        "IN_PROGRESS": [],
        "BLOCKED": [],
        "DONE": [],
        "CANCELLED": [],
    }

    for task in tasks:
        task_status = task.status or "TODO"
        if task_status in status_groups:
            status_groups[task_status].append(task)

    # 构建看板列
    columns = []
    status_names = {
        "TODO": "待办",
        "IN_PROGRESS": "进行中",
        "BLOCKED": "阻塞",
        "DONE": "已完成",
        "CANCELLED": "已取消",
    }

    for task_status, status_name in status_names.items():
        columns.append(
            ProgressBoardColumn(
                status=task_status,
                status_name=status_name,
                tasks=status_groups[task_status],
            )
        )

    # 汇总统计
    summary = {
        "total": len(tasks),
        "todo": len(status_groups["TODO"]),
        "in_progress": len(status_groups["IN_PROGRESS"]),
        "blocked": len(status_groups["BLOCKED"]),
        "done": len(status_groups["DONE"]),
        "cancelled": len(status_groups["CANCELLED"]),
    }

    return ProgressBoardResponse(
        project_id=project_id,
        project_name=project.project_name,
        columns=columns,
        summary=summary,
    )


# ==================== 机台进度汇总 ====================


@router.get(
    "/machines/{machine_id}/summary", response_model=MachineProgressSummaryResponse
)
def get_machine_progress_summary(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取机台进度汇总"""
    check_project_access_or_raise(db, current_user, project_id)

    machine = (
        db.query(Machine)
        .filter(Machine.id == machine_id, Machine.project_id == project_id)
        .first()
    )
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    # 获取机台的所有任务
    tasks = db.query(Task).filter(Task.machine_id == machine_id).all()

    if not tasks:
        return MachineProgressSummaryResponse(
            machine_id=machine_id,
            machine_name=machine.machine_name,
            machine_code=machine.machine_code,
            overall_progress=0.0,
            task_count=0,
            completed_count=0,
            in_progress_count=0,
            blocked_count=0,
        )

    # 计算整体进度
    total_weight = sum(float(task.weight) for task in tasks)
    weighted_progress = sum(
        float(task.weight) * task.progress_percent for task in tasks
    )
    overall_progress = (weighted_progress / total_weight) if total_weight > 0 else 0.0

    # 统计任务状态
    task_count = len(tasks)
    completed_count = len([t for t in tasks if t.status == "DONE"])
    in_progress_count = len([t for t in tasks if t.status == "IN_PROGRESS"])
    blocked_count = len([t for t in tasks if t.status == "BLOCKED"])

    return MachineProgressSummaryResponse(
        machine_id=machine_id,
        machine_name=machine.machine_name,
        machine_code=machine.machine_code,
        overall_progress=round(overall_progress, 2),
        task_count=task_count,
        completed_count=completed_count,
        in_progress_count=in_progress_count,
        blocked_count=blocked_count,
    )
