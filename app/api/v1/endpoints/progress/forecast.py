# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 智能化进度预测与依赖巡检
包含：进度预测、依赖巡检
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.models.progress import Task, TaskDependency
from app.schemas.progress import (
    ProgressForecastResponse, DependencyCheckResponse,
)
from app.schemas.common import ResponseModel
from .utils import (
    _build_project_forecast, _analyze_dependency_graph, _notify_dependency_alerts
)

router = APIRouter()


# ==================== 智能化进度预测与依赖巡检 ====================


@router.get(
    "/projects/{project_id}/progress-forecast",
    response_model=ResponseModel[ProgressForecastResponse],
    status_code=status.HTTP_200_OK
)
def get_project_progress_forecast(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """聚合项目任务的进度预测信息"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    tasks = (
        db.query(Task)
        .options(joinedload(Task.progress_logs))
        .filter(Task.project_id == project_id)
        .all()
    )

    forecast = _build_project_forecast(project, tasks)
    return ResponseModel(code=200, message="success", data=forecast)


@router.get(
    "/projects/{project_id}/dependency-check",
    response_model=ResponseModel[DependencyCheckResponse],
    status_code=status.HTTP_200_OK
)
def check_project_dependencies(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """执行任务依赖巡检，定位循环依赖、缺失依赖或计划冲突"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    task_map = {task.id: task for task in tasks}
    if task_map:
        dependencies = (
            db.query(TaskDependency)
            .filter(TaskDependency.task_id.in_(task_map.keys()))
            .all()
        )
    else:
        dependencies = []

    cycle_paths, issues = _analyze_dependency_graph(task_map, dependencies)
    _notify_dependency_alerts(db, project, task_map, cycle_paths, issues)
    response = DependencyCheckResponse(
        project_id=project.id,
        project_name=project.project_name,
        has_cycle=bool(cycle_paths),
        cycle_paths=cycle_paths,
        issues=issues
    )
    return ResponseModel(code=200, message="success", data=response)
