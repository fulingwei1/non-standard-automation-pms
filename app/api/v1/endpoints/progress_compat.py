# -*- coding: utf-8 -*-
"""Progress compatibility routes used by older tracking pages."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.progress import Task, TaskDependency, WbsTemplate, WbsTemplateTask
from app.models.project import Project, ProjectMilestone
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


def _decimal_to_float(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)
    return float(value or 0)


def _serialize_template(template: WbsTemplate) -> dict[str, Any]:
    return {
        "id": template.id,
        "template_code": template.template_code,
        "template_name": template.template_name,
        "project_type": template.project_type,
        "equipment_type": template.equipment_type,
        "version_no": template.version_no or "V1",
        "is_active": template.is_active if template.is_active is not None else True,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }


def _serialize_template_task(task: WbsTemplateTask) -> dict[str, Any]:
    return {
        "id": task.id,
        "template_id": task.template_id,
        "task_name": task.task_name,
        "stage": task.stage,
        "default_owner_role": task.default_owner_role,
        "plan_days": task.plan_days,
        "weight": _decimal_to_float(task.weight),
        "depends_on_template_task_id": task.depends_on_template_task_id,
    }


def _serialize_milestone(milestone: ProjectMilestone) -> dict[str, Any]:
    return {
        "id": milestone.id,
        "project_id": milestone.project_id,
        "project_name": milestone.project.project_name if milestone.project else None,
        "milestone_code": milestone.milestone_code,
        "milestone_name": milestone.milestone_name,
        "milestone_type": milestone.milestone_type,
        "planned_date": milestone.planned_date.isoformat() if milestone.planned_date else None,
        "actual_date": milestone.actual_date.isoformat() if milestone.actual_date else None,
        "status": milestone.status,
        "is_key": milestone.is_key if milestone.is_key is not None else False,
    }


def _serialize_task(task: Task) -> dict[str, Any]:
    return {
        "id": task.id,
        "project_id": task.project_id,
        "machine_id": task.machine_id,
        "milestone_id": task.milestone_id,
        "task_code": task.task_code,
        "task_name": task.task_name or f"任务#{task.id}",
        "name": task.task_name or f"任务#{task.id}",
        "stage": task.stage,
        "status": task.status or "TODO",
        "owner_id": task.owner_id,
        "assignee_id": task.owner_id,
        "owner_name": task.owner.display_name if task.owner else None,
        "assignee_name": task.owner.display_name if task.owner else None,
        "plan_start": task.plan_start.isoformat() if task.plan_start else None,
        "plan_end": task.plan_end.isoformat() if task.plan_end else None,
        "planned_start_date": task.plan_start.isoformat() if task.plan_start else None,
        "planned_end_date": task.plan_end.isoformat() if task.plan_end else None,
        "actual_start": task.actual_start.isoformat() if task.actual_start else None,
        "actual_end": task.actual_end.isoformat() if task.actual_end else None,
        "progress_percent": task.progress_percent or 0,
        "progress": task.progress_percent or 0,
        "weight": _decimal_to_float(task.weight),
        "block_reason": task.block_reason,
    }


def _project_planned_completion(project: Optional[Project], tasks: list[Task]) -> Optional[date]:
    for field in ("expected_end_date", "planned_end_date", "end_date"):
        value = getattr(project, field, None)
        if value:
            return value
    planned = [task.plan_end for task in tasks if task.plan_end]
    return max(planned) if planned else None


def _task_delay_days(task: Task) -> int:
    if task.actual_end and task.plan_end:
        return max((task.actual_end - task.plan_end).days, 0)
    if task.plan_end and (task.status or "TODO") not in {"DONE", "COMPLETED", "CANCELLED"}:
        return max((date.today() - task.plan_end).days, 0)
    return 0


def _load_project_tasks_for_auto(
    db: Session, current_user: User, project_id: int
) -> tuple[Project | None, list[Task]]:
    check_project_access_or_raise(db, current_user, project_id)
    project = db.query(Project).filter(Project.id == project_id).first()
    tasks = db.query(Task).filter(Task.project_id == project_id).order_by(Task.id).all()
    return project, tasks


def _dependency_issues_for_tasks(db: Session, tasks: list[Task]) -> list[dict[str, Any]]:
    task_map = {task.id: task for task in tasks}
    if not task_map:
        return []

    dependencies = (
        db.query(TaskDependency)
        .filter(TaskDependency.task_id.in_(task_map.keys()))
        .all()
    )
    issues: list[dict[str, Any]] = []
    for dependency in dependencies:
        task = task_map.get(dependency.task_id)
        predecessor = task_map.get(dependency.depends_on_task_id) or dependency.depends_on_task
        if not predecessor:
            issues.append(
                {
                    "issue_type": "MISSING_PREDECESSOR",
                    "severity": "MEDIUM",
                    "task_id": dependency.task_id,
                    "depends_on_task_id": dependency.depends_on_task_id,
                    "message": "前置任务不存在",
                }
            )
            continue
        if task and task.plan_start and predecessor.plan_end and predecessor.plan_end > task.plan_start:
            issues.append(
                {
                    "issue_type": "TIMING_CONFLICT",
                    "severity": "HIGH",
                    "task_id": task.id,
                    "depends_on_task_id": predecessor.id,
                    "message": "前置任务计划完成日晚于后续任务计划开始日",
                }
            )
    return issues


def _build_auto_preview(
    *,
    project_id: int,
    tasks: list[Task],
    auto_block: bool,
    delay_threshold: int,
    auto_fix_timing: bool,
    auto_fix_missing: bool,
    send_notifications: bool,
    db: Session,
) -> dict[str, Any]:
    delayed_tasks = [
        _serialize_task(task) | {"delay_days": _task_delay_days(task)}
        for task in tasks
    ]
    delayed_tasks = [task for task in delayed_tasks if task["delay_days"] > 0]
    will_block = [
        {
            "task_id": task["id"],
            "task_name": task["task_name"],
            "delay_days": task["delay_days"],
            "reason": f"预测延迟 {task['delay_days']} 天，超过阈值 {delay_threshold} 天",
        }
        for task in delayed_tasks
        if auto_block
        and task["delay_days"] > delay_threshold
        and task["status"] not in {"DONE", "COMPLETED", "CANCELLED"}
    ]
    dependency_issues = _dependency_issues_for_tasks(db, tasks)

    return {
        "project_id": project_id,
        "options": {
            "auto_block": auto_block,
            "delay_threshold": delay_threshold,
            "auto_fix_timing": auto_fix_timing,
            "auto_fix_missing": auto_fix_missing,
            "send_notifications": send_notifications,
        },
        "forecast_summary": {
            "task_count": len(tasks),
            "delayed_task_count": len(delayed_tasks),
            "will_block_count": len(will_block),
        },
        "dependency_summary": {
            "issue_count": len(dependency_issues),
            "timing_conflict_count": sum(
                1 for issue in dependency_issues if issue["issue_type"] == "TIMING_CONFLICT"
            ),
            "missing_predecessor_count": sum(
                1 for issue in dependency_issues if issue["issue_type"] == "MISSING_PREDECESSOR"
            ),
        },
        "preview_actions": {
            "will_block": will_block,
            "will_fix_timing": (
                sum(1 for issue in dependency_issues if issue["issue_type"] == "TIMING_CONFLICT")
                if auto_fix_timing
                else 0
            ),
            "will_remove_missing": (
                sum(1 for issue in dependency_issues if issue["issue_type"] == "MISSING_PREDECESSOR")
                if auto_fix_missing
                else 0
            ),
            "will_send_notifications": bool(send_notifications and (will_block or dependency_issues)),
        },
    }


def _apply_forecast_blocking(tasks: list[Task], auto_block: bool, delay_threshold: int) -> dict[str, int]:
    stats = {"total": len(tasks), "blocked": 0, "risk_tagged": 0, "skipped": 0}
    for task in tasks:
        delay_days = _task_delay_days(task)
        if delay_days <= delay_threshold or task.status in {"DONE", "COMPLETED", "CANCELLED"}:
            stats["skipped"] += 1
            continue
        if auto_block:
            task.status = "BLOCKED"
            task.block_reason = f"预测延迟 {delay_days} 天，超过阈值 {delay_threshold} 天"
            stats["blocked"] += 1
        else:
            stats["risk_tagged"] += 1
    return stats


def _remove_missing_dependencies(db: Session, tasks: list[Task], enabled: bool) -> int:
    if not enabled:
        return 0
    task_ids = [task.id for task in tasks]
    if not task_ids:
        return 0
    dependencies = db.query(TaskDependency).filter(TaskDependency.task_id.in_(task_ids)).all()
    existing_task_ids = set(task_ids)
    removed = 0
    for dependency in dependencies:
        if dependency.depends_on_task_id not in existing_task_ids and not dependency.depends_on_task:
            db.delete(dependency)
            removed += 1
    return removed


@router.get("/projects/{project_id}/tasks", response_model=PaginatedResponse[dict])
def list_project_tasks(
    project_id: int,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    task_status: Optional[str] = Query(None, alias="status"),
    stage: Optional[str] = Query(None),
    assignee_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    check_project_access_or_raise(db, current_user, project_id)
    query = db.query(Task).filter(Task.project_id == project_id)
    if task_status:
        query = query.filter(Task.status == task_status)
    if stage:
        query = query.filter(Task.stage == stage)
    if assignee_id:
        query = query.filter(Task.owner_id == assignee_id)
    if search:
        query = query.filter(Task.task_name.ilike(f"%{search}%"))

    total = query.count()
    rows = apply_pagination(
        query.order_by(Task.plan_start.is_(None), Task.plan_start, Task.id),
        pagination.offset,
        pagination.limit,
    ).all()
    return PaginatedResponse(
        items=[_serialize_task(row) for row in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


def _parse_optional_date(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


@router.post("/projects/{project_id}/tasks", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_project_task(
    project_id: int,
    task_in: dict[str, Any] = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    check_project_access_or_raise(db, current_user, project_id)

    task_name = str(task_in.get("task_name") or task_in.get("name") or "").strip()
    if not task_name:
        raise HTTPException(status_code=422, detail="task_name 不能为空")

    assigned_to = task_in.get("assigned_to")
    owner_id = task_in.get("owner_id") or task_in.get("assignee_id")
    if not owner_id and isinstance(assigned_to, list) and assigned_to:
        owner_id = assigned_to[0]

    task_count = db.query(Task).filter(Task.project_id == project_id).count()
    task = Task(
        project_id=project_id,
        machine_id=task_in.get("machine_id"),
        milestone_id=task_in.get("milestone_id"),
        task_code=task_in.get("task_code") or f"P{project_id}-T{task_count + 1:03d}",
        task_name=task_name,
        stage=task_in.get("stage"),
        status=task_in.get("status") or "TODO",
        owner_id=owner_id,
        plan_start=_parse_optional_date(
            task_in.get("plan_start")
            or task_in.get("planned_start_date")
            or task_in.get("start_date")
        ),
        plan_end=_parse_optional_date(
            task_in.get("plan_end")
            or task_in.get("planned_end_date")
            or task_in.get("end_date")
        ),
        weight=Decimal(str(task_in.get("weight") or "1.00")),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    payload = _serialize_task(task)
    if isinstance(assigned_to, list):
        payload["assigned_to"] = assigned_to
    elif owner_id:
        payload["assigned_to"] = [owner_id]
    else:
        payload["assigned_to"] = []
    return payload


@router.get("/tasks/{task_id}", response_model=dict)
def get_task(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    check_project_access_or_raise(db, current_user, task.project_id)
    return _serialize_task(task)


@router.get("/projects/{project_id}/progress-forecast", response_model=dict)
@router.get("/projects/{project_id}/forecast", response_model=dict)
def get_project_progress_forecast(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    check_project_access_or_raise(db, current_user, project_id)
    project = db.query(Project).filter(Project.id == project_id).first()
    tasks = db.query(Task).filter(Task.project_id == project_id).order_by(Task.id).all()
    progress_values = [task.progress_percent or 0 for task in tasks]
    current_progress = round(sum(progress_values) / len(progress_values), 2) if progress_values else 0
    delayed = [_serialize_task(task) | {"delay_days": _task_delay_days(task)} for task in tasks]
    delayed = [task for task in delayed if task["delay_days"] > 0]
    planned_completion = _project_planned_completion(project, tasks)
    predicted_delay_days = max((task["delay_days"] for task in delayed), default=0)
    predicted_completion = (
        planned_completion + timedelta(days=predicted_delay_days)
        if planned_completion
        else None
    )
    return {
        "project_id": project_id,
        "project_name": project.project_name if project else None,
        "planned_completion_date": planned_completion.isoformat() if planned_completion else None,
        "predicted_completion_date": predicted_completion.isoformat() if predicted_completion else None,
        "predicted_delay_days": predicted_delay_days,
        "forecast_horizon_days": 30,
        "expected_progress_next_7d": min(round(100 - current_progress, 2), 10),
        "expected_progress_next_14d": min(round(100 - current_progress, 2), 20),
        "confidence": "MEDIUM" if tasks else "LOW",
        "current_progress": current_progress,
        "tasks": delayed[:20],
    }


@router.get("/projects/{project_id}/dependency-check", response_model=dict)
def check_project_dependencies(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    from app.models.progress import TaskDependency

    check_project_access_or_raise(db, current_user, project_id)
    dependencies = (
        db.query(TaskDependency)
        .join(Task, TaskDependency.task_id == Task.id)
        .filter(Task.project_id == project_id)
        .all()
    )
    issues = []
    for dependency in dependencies:
        task = dependency.task
        predecessor = dependency.depends_on_task
        if not predecessor:
            issues.append(
                {
                    "issue_type": "MISSING_PREDECESSOR",
                    "severity": "MEDIUM",
                    "task_id": task.id if task else dependency.task_id,
                    "message": "前置任务不存在",
                }
            )
            continue
        if task and task.plan_start and predecessor.plan_end and predecessor.plan_end > task.plan_start:
            issues.append(
                {
                    "issue_type": "TIMING_CONFLICT",
                    "severity": "HIGH",
                    "task_id": task.id,
                    "depends_on_task_id": predecessor.id,
                    "message": "前置任务计划完成日晚于后续任务计划开始日",
                }
            )
    return {
        "project_id": project_id,
        "has_cycle": False,
        "cycle_paths": [],
        "issues": issues,
        "dependency_count": len(dependencies),
    }


@router.get("/projects/{project_id}/auto-preview", response_model=dict)
def preview_auto_processing(
    project_id: int,
    auto_block: bool = Query(False),
    delay_threshold: int = Query(7, ge=1),
    auto_fix_timing: bool = Query(False),
    auto_fix_missing: bool = Query(True),
    send_notifications: bool = Query(True),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """Preview automated progress actions without changing project data."""
    forecast = get_project_progress_forecast(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )
    dependency = check_project_dependencies(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )

    delayed_tasks = forecast.get("tasks") or []
    will_block = []
    if auto_block:
        for task in delayed_tasks:
            delay_days = int(task.get("delay_days") or 0)
            if delay_days > delay_threshold:
                will_block.append(
                    {
                        "task_id": task.get("id") or task.get("task_id"),
                        "task_name": task.get("task_name") or task.get("name"),
                        "reason": f"预测延期 {delay_days} 天，超过阈值 {delay_threshold} 天",
                    }
                )

    issues = dependency.get("issues") or []
    timing_conflicts = [
        issue for issue in issues if issue.get("issue_type") == "TIMING_CONFLICT"
    ]
    missing_predecessors = [
        issue for issue in issues if issue.get("issue_type") == "MISSING_PREDECESSOR"
    ]

    return {
        "success": True,
        "project_id": project_id,
        "options": {
            "auto_block": auto_block,
            "delay_threshold": delay_threshold,
            "auto_fix_timing": auto_fix_timing,
            "auto_fix_missing": auto_fix_missing,
            "send_notifications": send_notifications,
        },
        "forecast_stats": {
            "current_progress": forecast.get("current_progress", 0),
            "predicted_delay_days": forecast.get("predicted_delay_days", 0),
            "delayed_task_count": len(delayed_tasks),
        },
        "dependency_stats": {
            "dependency_count": dependency.get("dependency_count", 0),
            "issue_count": len(issues),
        },
        "preview_actions": {
            "will_block": will_block,
            "will_fix_timing": len(timing_conflicts) if auto_fix_timing else 0,
            "will_remove_missing": len(missing_predecessors) if auto_fix_missing else 0,
            "will_send_notifications": bool(send_notifications and (will_block or delayed_tasks)),
        },
    }


@router.post("/projects/{project_id}/auto-apply-forecast", response_model=dict)
def apply_forecast_auto_processing(
    project_id: int,
    auto_block: bool = Query(False),
    delay_threshold: int = Query(7, ge=1, le=60),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    _, tasks = _load_project_tasks_for_auto(db, current_user, project_id)
    stats = _apply_forecast_blocking(tasks, auto_block, delay_threshold)
    db.commit()
    return {"success": True, "project_id": project_id, "forecast_stats": stats}


@router.post("/projects/{project_id}/auto-fix-dependencies", response_model=dict)
def fix_dependencies_auto_processing(
    project_id: int,
    auto_fix_timing: bool = Query(False),
    auto_fix_missing: bool = Query(True),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    _, tasks = _load_project_tasks_for_auto(db, current_user, project_id)
    issues = _dependency_issues_for_tasks(db, tasks)
    removed = _remove_missing_dependencies(db, tasks, auto_fix_missing)
    db.commit()
    return {
        "success": True,
        "project_id": project_id,
        "dependency_stats": {
            "issue_count": len(issues),
            "timing_fixed": 0 if not auto_fix_timing else 0,
            "missing_removed": removed,
        },
    }


@router.post("/projects/{project_id}/auto-process-complete", response_model=dict)
def run_complete_auto_processing(
    project_id: int,
    options: Optional[dict[str, Any]] = Body(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    options = options or {}
    _, tasks = _load_project_tasks_for_auto(db, current_user, project_id)
    auto_block = bool(options.get("auto_block", False))
    delay_threshold = int(options.get("delay_threshold") or 7)
    auto_fix_timing = bool(options.get("auto_fix_timing", False))
    auto_fix_missing = bool(options.get("auto_fix_missing", True))
    send_notifications = bool(options.get("send_notifications", True))

    forecast_stats = _apply_forecast_blocking(tasks, auto_block, delay_threshold)
    issues = _dependency_issues_for_tasks(db, tasks)
    removed = _remove_missing_dependencies(db, tasks, auto_fix_missing)
    db.commit()

    return {
        "success": True,
        "project_id": project_id,
        "forecast_stats": forecast_stats,
        "dependency_stats": {
            "issue_count": len(issues),
            "timing_fixed": 0 if not auto_fix_timing else 0,
            "missing_removed": removed,
        },
        "notification_stats": {
            "forecast": {
                "skipped": "notification_dispatch_not_configured" if send_notifications else "disabled"
            }
        },
    }


@router.post("/projects/batch/auto-process", response_model=dict)
def batch_auto_process(
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    project_ids = payload.get("project_ids") or []
    options = payload.get("options") or {}
    results = []
    for raw_project_id in project_ids:
        project_id = int(raw_project_id)
        _, tasks = _load_project_tasks_for_auto(db, current_user, project_id)
        stats = _apply_forecast_blocking(
            tasks,
            bool(options.get("auto_block", False)),
            int(options.get("delay_threshold") or 7),
        )
        results.append({"project_id": project_id, "forecast_stats": stats})
    db.commit()
    return {"success": True, "processed": len(results), "results": results}


@router.get("/wbs-templates", response_model=PaginatedResponse[dict])
def list_wbs_templates(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    project_type: Optional[str] = Query(None),
    equipment_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    keyword: Optional[str] = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    query = db.query(WbsTemplate)

    if project_type:
        query = query.filter(WbsTemplate.project_type == project_type)
    if equipment_type:
        query = query.filter(WbsTemplate.equipment_type == equipment_type)
    if is_active is not None:
        query = query.filter(WbsTemplate.is_active == is_active)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            WbsTemplate.template_code.ilike(like) | WbsTemplate.template_name.ilike(like)
        )

    total = query.count()
    rows = apply_pagination(
        query.order_by(desc(WbsTemplate.id)),
        pagination.offset,
        pagination.limit,
    ).all()
    return PaginatedResponse(
        items=[_serialize_template(row) for row in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.post("/wbs-templates", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_wbs_template(
    data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    template = WbsTemplate(
        template_code=data.get("template_code"),
        template_name=data.get("template_name"),
        project_type=data.get("project_type"),
        equipment_type=data.get("equipment_type"),
        version_no=data.get("version_no") or "V1",
        is_active=data.get("is_active", True),
    )
    if not template.template_code or not template.template_name:
        raise HTTPException(status_code=400, detail="template_code 和 template_name 不能为空")

    db.add(template)
    db.commit()
    db.refresh(template)
    return _serialize_template(template)


@router.get("/wbs-templates/{template_id}", response_model=dict)
def get_wbs_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")
    return _serialize_template(template)


@router.put("/wbs-templates/{template_id}", response_model=dict)
def update_wbs_template(
    template_id: int,
    data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")

    for field in ["template_name", "project_type", "equipment_type", "version_no", "is_active"]:
        if field in data:
            setattr(template, field, data[field])
    db.commit()
    db.refresh(template)
    return _serialize_template(template)


@router.delete("/wbs-templates/{template_id}", response_model=dict)
def delete_wbs_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")
    db.delete(template)
    db.commit()
    return {"code": 200, "message": "删除成功"}


@router.get("/wbs-templates/{template_id}/tasks", response_model=list[dict])
def list_wbs_template_tasks(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    template = db.query(WbsTemplate.id).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")

    tasks = (
        db.query(WbsTemplateTask)
        .filter(WbsTemplateTask.template_id == template_id)
        .order_by(WbsTemplateTask.id)
        .all()
    )
    return [_serialize_template_task(task) for task in tasks]


@router.post(
    "/wbs-templates/{template_id}/tasks",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
def create_wbs_template_task(
    template_id: int,
    data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    if not db.query(WbsTemplate.id).filter(WbsTemplate.id == template_id).first():
        raise HTTPException(status_code=404, detail="WBS模板不存在")

    task = WbsTemplateTask(
        template_id=template_id,
        task_name=data.get("task_name"),
        stage=data.get("stage"),
        default_owner_role=data.get("default_owner_role"),
        plan_days=data.get("plan_days"),
        weight=data.get("weight", Decimal("1.00")),
        depends_on_template_task_id=data.get("depends_on_template_task_id"),
    )
    if not task.task_name:
        raise HTTPException(status_code=400, detail="task_name不能为空")
    db.add(task)
    db.commit()
    db.refresh(task)
    return _serialize_template_task(task)


@router.put("/wbs-template-tasks/{task_id}", response_model=dict)
def update_wbs_template_task(
    task_id: int,
    data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    task = db.query(WbsTemplateTask).filter(WbsTemplateTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="WBS模板任务不存在")
    for field in [
        "task_name",
        "stage",
        "default_owner_role",
        "plan_days",
        "weight",
        "depends_on_template_task_id",
    ]:
        if field in data:
            setattr(task, field, data[field])
    db.commit()
    db.refresh(task)
    return _serialize_template_task(task)


@router.get("/reports/milestone-rate", response_model=dict)
def get_milestone_rate_report(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    query = db.query(ProjectMilestone)
    if project_id:
        query = query.filter(ProjectMilestone.project_id == project_id)

    milestones = query.order_by(desc(ProjectMilestone.planned_date), desc(ProjectMilestone.id)).all()
    total = len(milestones)
    completed = sum(1 for item in milestones if item.status == "COMPLETED")
    overdue = sum(
        1
        for item in milestones
        if item.status != "COMPLETED" and item.planned_date and item.planned_date < date.today()
    )
    pending = max(total - completed, 0)
    project = db.query(Project).filter(Project.id == project_id).first() if project_id else None

    return {
        "project_id": project_id,
        "project_name": project.project_name if project else None,
        "total_milestones": total,
        "completed_milestones": completed,
        "completion_rate": round(completed / total * 100, 2) if total else 0,
        "overdue_milestones": overdue,
        "pending_milestones": pending,
        "milestones": [_serialize_milestone(item) for item in milestones[:100]],
    }


@router.get("/reports/delay-reasons", response_model=dict)
def get_delay_reasons_report(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None),
    top_n: int = Query(10, ge=1, le=50),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    query = db.query(Task).filter(Task.actual_end.isnot(None), Task.plan_end.isnot(None))
    query = query.filter(Task.actual_end > Task.plan_end)
    if project_id:
        query = query.filter(Task.project_id == project_id)

    delayed_tasks = query.all()
    total = len(delayed_tasks)
    reason_stats: dict[str, dict[str, Any]] = {}
    detailed_tasks = []

    for task in delayed_tasks:
        reason = task.block_reason or ("任务阻塞" if task.status == "BLOCKED" else "未填写原因")
        delay_days = max((task.actual_end - task.plan_end).days, 0)
        stat = reason_stats.setdefault(reason, {"reason": reason, "count": 0})
        stat["count"] += 1
        detailed_tasks.append(
            {
                "task_id": task.id,
                "task_name": task.task_name,
                "project_id": task.project_id,
                "assignee_name": task.owner.real_name if task.owner else "未分配",
                "delay_days": delay_days,
                "reason": reason,
            }
        )

    reasons = sorted(reason_stats.values(), key=lambda item: item["count"], reverse=True)[:top_n]
    for item in reasons:
        item["percentage"] = round(item["count"] / total * 100, 2) if total else 0

    return {
        "project_id": project_id,
        "total_delayed_tasks": total,
        "reasons": reasons,
        "detailed_tasks": detailed_tasks[:200],
    }
