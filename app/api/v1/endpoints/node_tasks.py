# -*- coding: utf-8 -*-
"""
节点子任务 API
提供节点子任务的 CRUD、状态流转、进度查询等接口
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.stage_template import (
    BatchCreateTasksRequest,
    NodeTaskComplete,
    NodeTaskCreate,
    NodeTaskProgressResponse,
    NodeTaskResponse,
    NodeTaskUpdate,
    ReorderTasksRequest,
)
from app.services.node_task_service import NodeTaskService

router = APIRouter()


# ==================== 任务 CRUD ====================


@router.post("/", response_model=NodeTaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: NodeTaskCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:create")),
) -> Any:
    """创建子任务"""
    service = NodeTaskService(db)
    try:
        task = service.create_task(
            node_instance_id=task_in.node_instance_id,
            task_name=task_in.task_name,
            task_code=task_in.task_code,
            description=task_in.description,
            estimated_hours=task_in.estimated_hours,
            planned_start_date=task_in.planned_start_date,
            planned_end_date=task_in.planned_end_date,
            assignee_id=task_in.assignee_id,
            priority=task_in.priority,
            tags=task_in.tags,
            created_by=current_user.id,
        )
        db.commit()
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 用户任务查询 ====================
# 注意：固定路径必须在参数化路径之前，否则会被参数化路径匹配


@router.get("/my-tasks", response_model=List[NodeTaskResponse])
def get_my_tasks(
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """获取当前用户的任务列表"""
    service = NodeTaskService(db)
    return service.get_user_tasks(current_user.id, project_id, status)


@router.get("/user/{user_id}", response_model=List[NodeTaskResponse])
def get_user_tasks(
    user_id: int,
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """获取用户的任务列表（跨节点）"""
    service = NodeTaskService(db)
    return service.get_user_tasks(user_id, project_id, status)


@router.get("/{task_id}", response_model=NodeTaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """获取任务详情"""
    service = NodeTaskService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.put("/{task_id}", response_model=NodeTaskResponse)
def update_task(
    task_id: int,
    task_in: NodeTaskUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:update")),
) -> Any:
    """更新任务"""
    service = NodeTaskService(db)
    task = service.update_task(task_id, **task_in.model_dump(exclude_unset=True))
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.commit()
    return task


@router.delete("/{task_id}", response_model=MessageResponse)
def delete_task(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:update")),
) -> Any:
    """删除任务"""
    service = NodeTaskService(db)
    success = service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.commit()
    return {"message": "删除成功"}


# ==================== 节点任务列表 ====================


@router.get("/node/{node_instance_id}", response_model=List[NodeTaskResponse])
def list_node_tasks(
    node_instance_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    assignee_id: Optional[int] = Query(None, description="执行人筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """获取节点的任务列表"""
    service = NodeTaskService(db)
    return service.list_tasks(node_instance_id, status, assignee_id)


@router.get("/node/{node_instance_id}/progress", response_model=NodeTaskProgressResponse)
def get_node_task_progress(
    node_instance_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """获取节点任务进度"""
    service = NodeTaskService(db)
    return service.get_node_task_progress(node_instance_id)


@router.post("/node/{node_instance_id}/batch", response_model=List[NodeTaskResponse], status_code=status.HTTP_201_CREATED)
def batch_create_tasks(
    node_instance_id: int,
    batch_in: BatchCreateTasksRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:update")),
) -> Any:
    """批量创建任务"""
    service = NodeTaskService(db)
    try:
        tasks_data = [t.model_dump() for t in batch_in.tasks]
        tasks = service.batch_create_tasks(
            node_instance_id=node_instance_id,
            tasks_data=tasks_data,
            created_by=current_user.id,
        )
        db.commit()
        return tasks
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/node/{node_instance_id}/reorder", response_model=MessageResponse)
def reorder_tasks(
    node_instance_id: int,
    reorder_in: ReorderTasksRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:update")),
) -> Any:
    """重新排序任务"""
    service = NodeTaskService(db)
    service.reorder_tasks(node_instance_id, reorder_in.task_ids)
    db.commit()
    return {"message": "排序成功"}


# ==================== 任务状态流转 ====================


@router.post("/{task_id}/start", response_model=NodeTaskResponse)
def start_task(
    task_id: int,
    actual_start_date: Optional[date] = Query(None, description="实际开始日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:update")),
) -> Any:
    """开始任务"""
    service = NodeTaskService(db)
    try:
        task = service.start_task(task_id, actual_start_date)
        db.commit()
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/complete", response_model=NodeTaskResponse)
def complete_task(
    task_id: int,
    complete_in: NodeTaskComplete,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:update")),
) -> Any:
    """完成任务"""
    service = NodeTaskService(db)
    try:
        task = service.complete_task(
            task_id=task_id,
            completed_by=current_user.id,
            actual_hours=complete_in.actual_hours,
            attachments=complete_in.attachments,
            remark=complete_in.remark,
        )
        db.commit()
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/skip", response_model=NodeTaskResponse)
def skip_task(
    task_id: int,
    reason: Optional[str] = Query(None, description="跳过原因"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:update")),
) -> Any:
    """跳过任务"""
    service = NodeTaskService(db)
    try:
        task = service.skip_task(task_id, reason)
        db.commit()
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 任务分配 ====================


@router.put("/{task_id}/assign", response_model=NodeTaskResponse)
def assign_task(
    task_id: int,
    assignee_id: int = Query(..., description="执行人ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:update")),
) -> Any:
    """分配任务"""
    service = NodeTaskService(db)
    try:
        task = service.assign_task(task_id, assignee_id)
        db.commit()
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{task_id}/priority", response_model=NodeTaskResponse)
def set_task_priority(
    task_id: int,
    priority: str = Query(..., description="优先级: LOW/NORMAL/HIGH/URGENT"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:update")),
) -> Any:
    """设置任务优先级"""
    service = NodeTaskService(db)
    try:
        task = service.set_task_priority(task_id, priority)
        db.commit()
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
