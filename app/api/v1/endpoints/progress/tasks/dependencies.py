# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 任务依赖管理
包含：任务依赖关系的查询、创建、删除
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.progress import Task, TaskDependency
from app.models.user import User
from app.schemas.progress import TaskDependencyCreate, TaskDependencyResponse

router = APIRouter()


@router.get("/tasks/{task_id}/dependencies", response_model=List[TaskDependencyResponse], status_code=status.HTTP_200_OK)
def read_task_dependencies(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取任务依赖关系（前置任务）
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    dependencies = db.query(TaskDependency).filter(TaskDependency.task_id == task_id).all()

    # 补充依赖任务名称
    result = []
    for dep in dependencies:
        depends_task = db.query(Task).filter(Task.id == dep.depends_on_task_id).first()
        dep_dict = {
            "id": dep.id,
            "task_id": dep.task_id,
            "depends_on_task_id": dep.depends_on_task_id,
            "dependency_type": dep.dependency_type,
            "lag_days": dep.lag_days,
            "depends_on_task_name": depends_task.task_name if depends_task else None
        }
        result.append(dep_dict)

    return result


@router.post("/tasks/{task_id}/dependencies", response_model=TaskDependencyResponse, status_code=status.HTTP_201_CREATED)
def create_task_dependency(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    dependency_in: TaskDependencyCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    设置任务依赖关系
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证依赖的任务是否存在且属于同一项目
    depends_task = db.query(Task).filter(Task.id == dependency_in.depends_on_task_id).first()
    if not depends_task:
        raise HTTPException(status_code=404, detail="依赖的任务不存在")

    if depends_task.project_id != task.project_id:
        raise HTTPException(status_code=400, detail="依赖的任务必须属于同一项目")

    # 检查是否已存在该依赖
    existing = db.query(TaskDependency).filter(
        TaskDependency.task_id == task_id,
        TaskDependency.depends_on_task_id == dependency_in.depends_on_task_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该依赖关系已存在")

    # 检查循环依赖
    if dependency_in.depends_on_task_id == task_id:
        raise HTTPException(status_code=400, detail="任务不能依赖自身")

    dependency = TaskDependency(
        task_id=task_id,
        depends_on_task_id=dependency_in.depends_on_task_id,
        dependency_type=dependency_in.dependency_type,
        lag_days=dependency_in.lag_days
    )
    db.add(dependency)
    db.commit()
    db.refresh(dependency)

    # 补充依赖任务名称
    dependency_dict = {
        "id": dependency.id,
        "task_id": dependency.task_id,
        "depends_on_task_id": dependency.depends_on_task_id,
        "dependency_type": dependency.dependency_type,
        "lag_days": dependency.lag_days,
        "depends_on_task_name": depends_task.task_name
    }

    return dependency_dict


@router.delete("/task-dependencies/{dependency_id}", status_code=status.HTTP_200_OK)
def delete_task_dependency(
    *,
    db: Session = Depends(deps.get_db),
    dependency_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除任务依赖关系
    """
    dependency = db.query(TaskDependency).filter(TaskDependency.id == dependency_id).first()
    if not dependency:
        raise HTTPException(status_code=404, detail="依赖关系不存在")

    db.delete(dependency)
    db.commit()

    return {"message": "依赖关系已删除", "id": dependency_id}
