# -*- coding: utf-8 -*-
"""
Field Commissioning 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import Body, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.field_commissioning import FieldCheckin, FieldIssue, FieldTask
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


def _dt(value: Any) -> Optional[str]:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return None if value is None else str(value)


def _task_to_dict(task: FieldTask) -> dict[str, Any]:
    return {
        "id": task.id,
        "task_no": task.task_no,
        "customer_name": task.customer_name,
        "project_name": task.project_name,
        "address": task.address,
        "status": task.status,
        "assigned_to": task.assigned_to,
        "scheduled_date": _dt(task.scheduled_date),
        "progress": task.progress or 0,
        "progress_note": task.progress_note,
        "completion_signature": task.completion_signature,
        "completion_time": _dt(task.completion_time),
        "created_at": _dt(task.created_at),
        "updated_at": _dt(task.updated_at),
    }


def _get_task_or_404(db: Session, task_id: int) -> FieldTask:
    task = db.query(FieldTask).filter(FieldTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="现场调试任务不存在")
    return task


def _current_user_key(current_user: User) -> str:
    value = getattr(current_user, "id", None) or getattr(current_user, "username", None)
    return str(value or "unknown")


def _payload_float(data: dict, key: str) -> float:
    if key not in data or data[key] is None:
        raise HTTPException(status_code=400, detail=f"{key} 不能为空")
    try:
        return float(data[key])
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"{key} 必须是数字") from exc


def _payload_progress(data: dict) -> int:
    raw = data.get("progress", data.get("progress_pct", data.get("percent")))
    if raw is None:
        raise HTTPException(status_code=400, detail="progress 不能为空")
    try:
        progress = int(raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="progress 必须是 0-100 的整数") from exc
    if progress < 0 or progress > 100:
        raise HTTPException(status_code=400, detail="progress 必须在 0-100 之间")
    return progress


def _issue_description(data: dict) -> str:
    title = data.get("title")
    description = data.get("description") or data.get("issue") or data.get("content") or data.get("note")
    if not description or not str(description).strip():
        raise HTTPException(status_code=400, detail="description 不能为空")
    description = str(description).strip()
    if title and str(title).strip() and str(title).strip() not in description:
        return f"{str(title).strip()}：{description}"
    return description


def _photo_url(data: dict) -> Optional[str]:
    photo_url = data.get("photo_url") or data.get("photo")
    photos = data.get("photos")
    if not photo_url and isinstance(photos, list) and photos:
        photo_url = photos[0]
    return str(photo_url) if photo_url else None


@router.get("/field/tasks")
def list_field_tasks(
    status: Optional[str] = Query(None, description="状态筛选"),
    assigned_to: Optional[str] = Query(None, description="负责人筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> list[dict]:
    """现场调试任务列表兼容接口。"""
    query = db.query(FieldTask)
    if status:
        query = query.filter(FieldTask.status == status)
    if assigned_to:
        query = query.filter(FieldTask.assigned_to == assigned_to)
    tasks = query.order_by(FieldTask.scheduled_date.asc(), FieldTask.id.asc()).limit(200).all()
    return [_task_to_dict(task) for task in tasks]


@router.get("/field/dashboard")
def get_field_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> dict:
    """现场调试概览兼容接口。"""
    today = date.today()
    status_rows = db.query(FieldTask.status, func.count(FieldTask.id)).group_by(FieldTask.status).all()
    status_counts = {status or "pending": count for status, count in status_rows}
    today_tasks = (
        db.query(func.count(FieldTask.id))
        .filter(FieldTask.scheduled_date == today)
        .scalar()
        or 0
    )
    open_issues = (
        db.query(func.count(FieldIssue.id))
        .filter(FieldIssue.status.in_(("open", "in_progress")))
        .scalar()
        or 0
    )
    return {
        "today_tasks": today_tasks,
        "pending": status_counts.get("pending", 0),
        "in_progress": status_counts.get("in_progress", 0),
        "completed": status_counts.get("completed", 0),
        "cancelled": status_counts.get("cancelled", 0),
        "issues": open_issues,
        "date": today.isoformat(),
    }


@router.get("/field/tasks/{task_id}")
def get_field_task(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> dict:
    task = _get_task_or_404(db, task_id)
    return _task_to_dict(task)


@router.post("/field/tasks/{task_id}/checkin", response_model=ResponseModel)
def checkin_field_task(
    task_id: int,
    data: dict = Body(default_factory=dict),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    task = _get_task_or_404(db, task_id)
    now = datetime.now()
    checkin = FieldCheckin(
        task_id=task.id,
        user_id=_current_user_key(current_user),
        latitude=_payload_float(data, "latitude"),
        longitude=_payload_float(data, "longitude"),
        checkin_time=now,
    )
    db.add(checkin)
    if task.status == "pending":
        task.status = "in_progress"
    task.updated_at = now
    db.commit()
    db.refresh(checkin)
    db.refresh(task)
    return ResponseModel(
        code=200,
        message="签到已记录",
        data={
            "id": checkin.id,
            "task_id": task.id,
            "checked_in_at": checkin.checkin_time.isoformat(),
            "status": task.status,
        },
    )


@router.post("/field/tasks/{task_id}/progress", response_model=ResponseModel)
def update_field_task_progress(
    task_id: int,
    data: dict = Body(default_factory=dict),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    task = _get_task_or_404(db, task_id)
    progress = _payload_progress(data)
    now = datetime.now()
    task.progress = progress
    task.progress_note = data.get("note") or data.get("progress_note") or task.progress_note
    if task.status != "completed":
        task.status = "completed" if progress == 100 else "in_progress"
    if progress == 100 and task.completion_time is None:
        task.completion_time = now
    task.updated_at = now
    db.commit()
    db.refresh(task)
    return ResponseModel(code=200, message="进度已更新", data=_task_to_dict(task))


@router.post("/field/tasks/{task_id}/issue", response_model=ResponseModel)
def report_field_task_issue(
    task_id: int,
    data: dict = Body(default_factory=dict),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    task = _get_task_or_404(db, task_id)
    severity = str(data.get("severity") or "medium").lower()
    if severity not in {"low", "medium", "high", "critical"}:
        raise HTTPException(status_code=400, detail="severity 必须是 low/medium/high/critical")
    now = datetime.now()
    description = _issue_description(data)
    issue = FieldIssue(
        task_id=task.id,
        description=description,
        photo_url=_photo_url(data),
        severity=severity,
        status="open",
        reported_by=_current_user_key(current_user),
        reported_at=now,
    )
    db.add(issue)
    task.progress_note = description
    if task.status == "pending":
        task.status = "in_progress"
    task.updated_at = now
    db.commit()
    db.refresh(issue)
    db.refresh(task)
    return ResponseModel(
        code=200,
        message="问题已记录",
        data={
            "id": issue.id,
            "task_id": task.id,
            "description": issue.description,
            "severity": issue.severity,
            "status": issue.status,
            "reported_at": issue.reported_at.isoformat() if issue.reported_at else None,
        },
    )


@router.post("/field/tasks/{task_id}/complete", response_model=ResponseModel)
def complete_field_task(
    task_id: int,
    data: dict = Body(default_factory=dict),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    task = _get_task_or_404(db, task_id)
    now = datetime.now()
    task.status = "completed"
    task.progress = 100
    task.progress_note = (
        data.get("note")
        or data.get("progress_note")
        or data.get("completion_note")
        or task.progress_note
    )
    task.completion_signature = (
        data.get("signature")
        or data.get("completion_signature")
        or data.get("customer_signature")
        or task.completion_signature
    )
    task.completion_time = now
    task.updated_at = now
    db.commit()
    db.refresh(task)
    return ResponseModel(
        code=200,
        message="任务已完成",
        data={"task_id": task.id, "completed_at": task.completion_time.isoformat(), **_task_to_dict(task)},
    )
