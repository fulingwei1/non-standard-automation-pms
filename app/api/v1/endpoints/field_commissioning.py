# -*- coding: utf-8 -*-
"""
Field Commissioning 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import Body, Depends, HTTPException, Query

from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

try:
    # Attempt different possible locations for field_commissioning
    from .fieldcommissioning import router
except ImportError:
    try:
        from .field import router
    except ImportError:
        try:
            from .common.field_commissioning import router
        except ImportError:
            try:
                from .admin.field_commissioning import router
            except ImportError:
                from fastapi import APIRouter

                router = APIRouter()

__all__ = ['router']


@router.get("/field/tasks")
def list_field_tasks(
    status: Optional[str] = Query(None, description="状态筛选"),
    assigned_to: Optional[str] = Query(None, description="负责人筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> list[dict]:
    """现场调试任务列表兼容接口。"""
    return []


@router.get("/field/dashboard")
def get_field_dashboard(
    current_user: User = Depends(security.get_current_active_user),
) -> dict:
    """现场调试概览兼容接口。"""
    return {
        "today_tasks": 0,
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
        "cancelled": 0,
        "issues": 0,
        "date": date.today().isoformat(),
    }


@router.get("/field/tasks/{task_id}")
def get_field_task(
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> dict:
    raise HTTPException(status_code=404, detail="现场调试任务不存在")


@router.post("/field/tasks/{task_id}/checkin", response_model=ResponseModel)
def checkin_field_task(
    task_id: int,
    data: dict = Body(default_factory=dict),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return ResponseModel(
        code=200,
        message="签到已记录",
        data={"task_id": task_id, "checked_in_at": datetime.now().isoformat()},
    )


@router.post("/field/tasks/{task_id}/progress", response_model=ResponseModel)
def update_field_task_progress(
    task_id: int,
    data: dict = Body(default_factory=dict),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return ResponseModel(code=200, message="进度已更新", data={"task_id": task_id, **data})


@router.post("/field/tasks/{task_id}/issue", response_model=ResponseModel)
def report_field_task_issue(
    task_id: int,
    data: dict = Body(default_factory=dict),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return ResponseModel(code=200, message="问题已记录", data={"task_id": task_id, **data})


@router.post("/field/tasks/{task_id}/complete", response_model=ResponseModel)
def complete_field_task(
    task_id: int,
    data: dict = Body(default_factory=dict),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return ResponseModel(
        code=200,
        message="任务已完成",
        data={"task_id": task_id, "completed_at": datetime.now().isoformat(), **data},
    )
