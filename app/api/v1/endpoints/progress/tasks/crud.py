# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 任务CRUD操作
包含：任务列表查询、创建、读取、更新、删除
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.progress import Task
from app.models.project import Machine, Project, ProjectMilestone
from app.models.user import User
from app.schemas.progress import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from app.services.data_scope_service import DataScopeConfig, DataScopeService

router = APIRouter()

# 任务数据权限配置
TASK_DATA_SCOPE_CONFIG = DataScopeConfig(
    owner_field="owner_id",
    project_field="project_id",
)


@router.get("/projects/{project_id}/tasks", response_model=TaskListResponse, status_code=status.HTTP_200_OK)
def read_project_tasks(
    project_id: int,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    milestone_id: Optional[int] = Query(None, description="里程碑ID筛选"),
    stage: Optional[str] = Query(None, description="阶段筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目任务列表（按数据权限过滤）
    """
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    query = db.query(Task).filter(Task.project_id == project_id)

    # 应用数据权限过滤
    query = DataScopeService.filter_by_scope(
        db, query, Task, current_user, TASK_DATA_SCOPE_CONFIG
    )

    # 机台筛选
    if machine_id:
        query = query.filter(Task.machine_id == machine_id)

    # 里程碑筛选
    if milestone_id:
        query = query.filter(Task.milestone_id == milestone_id)

    # 阶段筛选
    if stage:
        query = query.filter(Task.stage == stage)

    # 状态筛选
    if status_filter:
        query = query.filter(Task.status == status_filter)

    # 负责人筛选
    if owner_id:
        query = query.filter(Task.owner_id == owner_id)

    # 计算总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    tasks = query.order_by(Task.plan_start.asc(), Task.id.asc()).offset(offset).limit(page_size).all()

    return TaskListResponse(
        items=tasks,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_project_task(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    task_in: TaskCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建项目任务
    """
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 验证机台（如果提供）
    if task_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == task_in.machine_id).first()
        if not machine or machine.project_id != project_id:
            raise HTTPException(status_code=400, detail="机台不存在或不属于该项目")

    # 验证里程碑（如果提供）
    if task_in.milestone_id:
        milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == task_in.milestone_id).first()
        if not milestone or milestone.project_id != project_id:
            raise HTTPException(status_code=400, detail="里程碑不存在或不属于该项目")

    task = Task(project_id=project_id, status="TODO", **task_in.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get("/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def read_task(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取任务详情
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def update_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目任务
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    update_data = task_in.model_dump(exclude_unset=True)

    # 如果更新状态为IN_PROGRESS且actual_start为空，自动设置
    if update_data.get("status") == "IN_PROGRESS" and not task.actual_start:
        update_data["actual_start"] = date.today()

    # 如果更新状态为DONE且actual_end为空，自动设置
    if update_data.get("status") == "DONE" and not task.actual_end:
        update_data["actual_end"] = date.today()
        if "progress_percent" not in update_data:
            update_data["progress_percent"] = 100

    for field, value in update_data.items():
        setattr(task, field, value)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除任务（软删除，仅管理员）
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 权限检查：仅管理员可以删除
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权删除任务，仅管理员可操作")

    # 检查是否有依赖此任务的其他任务
    from app.models.progress import TaskDependency
    dependent_tasks = db.query(TaskDependency).filter(
        TaskDependency.depends_on_task_id == task_id
    ).count()

    if dependent_tasks > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除任务，有 {dependent_tasks} 个任务依赖此任务"
        )

    # 删除任务及其关联数据（依赖关系、进度日志等会通过cascade自动删除）
    db.delete(task)
    db.commit()

    return {"message": "任务已删除", "id": task_id}
