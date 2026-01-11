# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 公共工具函数
"""

from typing import Dict, List, Tuple, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import math

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.progress import Task, TaskDependency
from app.models.notification import Notification
from app.schemas.progress import (
    TaskForecastItem, ProgressForecastResponse, DependencyIssue
)
from app.services.sales_reminder_service import create_notification


def _calculate_task_forecast(task: Task, today: Optional[date] = None) -> Tuple[TaskForecastItem, bool]:
    """Estimate task finish date based on progress history."""
    if today is None:
        today = date.today()

    progress_logs = sorted(
        getattr(task, "progress_logs", []) or [],
        key=lambda log: log.updated_at or datetime.combine(today, datetime.min.time())
    )
    has_history = len(progress_logs) >= 2

    progress = task.progress_percent or 0
    plan_end = task.plan_end
    plan_start = task.plan_start
    plan_duration = None
    if plan_start and plan_end:
        plan_duration = max((plan_end - plan_start).days, 1)

    rate = None
    if len(progress_logs) >= 2:
        earliest, latest = progress_logs[0], progress_logs[-1]
        delta_days = max((latest.updated_at.date() - earliest.updated_at.date()).days, 1)
        delta_progress = max(latest.progress_percent - earliest.progress_percent, 0)
        if delta_progress > 0 and delta_days > 0:
            rate = delta_progress / delta_days

    if rate is None and task.actual_start and progress > 0:
        elapsed = max((today - task.actual_start).days, 1)
        rate = progress / elapsed

    if rate is None and plan_duration:
        rate = 100 / plan_duration

    if rate is None or rate <= 0:
        rate = 5.0  # fallback velocity

    predicted_finish = plan_end or today
    delay_days = None
    status = "OnTrack"
    critical = False

    if progress >= 100:
        predicted_finish = task.actual_end or plan_end or today
        status = "Completed" if (task.status or "").upper() == "DONE" else "Finishing"
        remaining_days = 0
        rate_value = None
    else:
        remaining = max(100 - progress, 0)
        remaining_days = math.ceil(remaining / max(rate, 0.1))
        predicted_finish = today + timedelta(days=remaining_days)
        rate_value = float(rate)
        if plan_end:
            delay_days = (predicted_finish - plan_end).days
            if delay_days > 0:
                status = "Delayed"
                critical = True

    item = TaskForecastItem(
        task_id=task.id,
        task_name=task.task_name,
        progress_percent=progress,
        predicted_finish_date=predicted_finish,
        plan_end=plan_end,
        delay_days=delay_days,
        status=status,
        critical=critical,
        rate_per_day=rate_value,
        weight=float(task.weight or Decimal("1.0"))
    )
    return item, has_history


def _build_project_forecast(project: Project, tasks: List[Task], today: Optional[date] = None) -> ProgressForecastResponse:
    """Aggregate task forecasts into project level insight."""
    if today is None:
        today = date.today()

    if not tasks:
        return ProgressForecastResponse(
            project_id=project.id,
            project_name=project.project_name,
            current_progress=0.0,
            predicted_completion_date=today,
            planned_completion_date=today,
            predicted_delay_days=0,
            forecast_horizon_days=0,
            confidence="LOW",
            expected_progress_next_7d=0.0,
            expected_progress_next_14d=0.0,
            tasks=[]
        )

    forecasts: List[TaskForecastItem] = []
    history_count = 0
    total_weight = 0.0
    weighted_progress = 0.0

    for task in tasks:
        forecast, has_history = _calculate_task_forecast(task, today)
        forecasts.append(forecast)
        total_weight += forecast.weight
        weighted_progress += forecast.weight * forecast.progress_percent
        if has_history:
            history_count += 1

    total_weight = total_weight or 1.0
    current_progress = weighted_progress / total_weight

    predicted_completion_date = max(f.predicted_finish_date for f in forecasts)
    planned_completion_candidates = [f.plan_end for f in forecasts if f.plan_end]
    planned_completion_date = max(planned_completion_candidates) if planned_completion_candidates else predicted_completion_date
    predicted_delay_days = (predicted_completion_date - planned_completion_date).days if planned_completion_date else 0
    forecast_horizon_days = max((predicted_completion_date - today).days, 0)

    def _expected_gain(days: int) -> float:
        delta = 0.0
        for f in forecasts:
            if not f.rate_per_day:
                continue
            remaining = max(100 - f.progress_percent, 0)
            expected = min(f.rate_per_day * days, remaining)
            delta += expected * f.weight
        return (delta / total_weight) if total_weight else 0.0

    expected_progress_next_7d = _expected_gain(7)
    expected_progress_next_14d = _expected_gain(14)

    history_ratio = history_count / len(forecasts)
    if history_ratio >= 0.6:
        confidence = "HIGH"
    elif history_ratio >= 0.3:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return ProgressForecastResponse(
        project_id=project.id,
        project_name=project.project_name,
        current_progress=round(current_progress, 2),
        predicted_completion_date=predicted_completion_date,
        planned_completion_date=planned_completion_date,
        predicted_delay_days=predicted_delay_days,
        forecast_horizon_days=forecast_horizon_days,
        confidence=confidence,
        expected_progress_next_7d=round(expected_progress_next_7d, 2),
        expected_progress_next_14d=round(expected_progress_next_14d, 2),
        tasks=forecasts
    )


def _analyze_dependency_graph(tasks: Dict[int, Task], dependencies: List[TaskDependency]) -> Tuple[List[List[str]], List[DependencyIssue]]:
    """Look for cycles, missing links, and invalid timing relationships."""
    graph: Dict[int, List[int]] = defaultdict(list)
    issues: List[DependencyIssue] = []

    for dep in dependencies:
        if dep.task_id not in tasks:
            continue
        if dep.depends_on_task_id not in tasks:
            issues.append(DependencyIssue(
                issue_type="MISSING_PREDECESSOR",
                severity="HIGH",
                task_id=dep.task_id,
                task_name=tasks[dep.task_id].task_name,
                detail=f"依赖的任务ID {dep.depends_on_task_id} 不存在"
            ))
            continue
        graph[dep.task_id].append(dep.depends_on_task_id)

    cycles: List[List[int]] = []
    temp_mark = set()
    perm_mark = set()
    stack: List[int] = []

    def _dfs(node: int):
        if node in perm_mark:
            return
        temp_mark.add(node)
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt in temp_mark:
                cycle_start = stack.index(nxt)
                cycle = stack[cycle_start:] + [nxt]
                cycles.append(cycle)
            else:
                _dfs(nxt)
        stack.pop()
        temp_mark.remove(node)
        perm_mark.add(node)

    for task_id in tasks.keys():
        if task_id not in perm_mark:
            _dfs(task_id)

    dependency_type = {
        "FS": "先完成后开始",
        "SS": "同时开始",
        "FF": "同时完成",
        "SF": "先开始后完成"
    }

    for dep in dependencies:
        if dep.task_id not in tasks or dep.depends_on_task_id not in tasks:
            continue
        successor = tasks[dep.task_id]
        predecessor = tasks[dep.depends_on_task_id]
        lag = dep.lag_days or 0

        pred_finish = predecessor.actual_end or predecessor.plan_end
        succ_start = successor.actual_start or successor.plan_start
        succ_finish = successor.actual_end or successor.plan_end
        pred_start = predecessor.actual_start or predecessor.plan_start

        dep_label = dependency_type.get(dep.dependency_type, dep.dependency_type)

        def _add_issue(detail: str, severity: str = "MEDIUM"):
            issues.append(DependencyIssue(
                issue_type="TIMING_CONFLICT",
                severity=severity,
                task_id=successor.id,
                task_name=successor.task_name,
                detail=f"{dep_label} 约束违反: {detail}"
            ))

        if dep.dependency_type == "FS" and pred_finish and succ_start:
            if succ_start < (pred_finish + timedelta(days=lag)):
                _add_issue(f"{successor.task_name} 在前置任务完成前开始")
        elif dep.dependency_type == "SS" and pred_start and succ_start:
            if succ_start < (pred_start + timedelta(days=lag)):
                _add_issue(f"{successor.task_name} 早于前置任务开始")
        elif dep.dependency_type == "FF" and pred_finish and succ_finish:
            if succ_finish < (pred_finish + timedelta(days=lag)):
                _add_issue(f"{successor.task_name} 早于前置任务完成")
        elif dep.dependency_type == "SF" and pred_start and succ_finish:
            if succ_finish < (pred_start + timedelta(days=lag)):
                _add_issue(f"{successor.task_name} 在前置任务开始前完成")

        pred_complete = (predecessor.progress_percent or 0) >= 100 or (predecessor.status or "").upper() == "DONE"
        succ_started = (successor.status or "").upper() in {"IN_PROGRESS", "DONE"} or successor.actual_start is not None

        if succ_started and not pred_complete:
            issues.append(DependencyIssue(
                issue_type="UNRESOLVED_PREDECESSOR",
                severity="HIGH",
                task_id=successor.id,
                task_name=successor.task_name,
                detail=f"{successor.task_name} 已启动，但前置任务 {predecessor.task_name} 未完成"
            ))

    cycle_paths: List[List[str]] = []
    for path in cycles:
        readable = []
        for task_id in path:
            task = tasks.get(task_id)
            readable.append(task.task_name if task else f"Task {task_id}")
        cycle_paths.append(readable)

    return cycle_paths, issues


def _notify_dependency_alerts(
    db: Session,
    project: Project,
    task_map: Dict[int, Task],
    cycle_paths: List[List[str]],
    issues: List[DependencyIssue],
) -> None:
    """Persist notifications when high severity dependency issues exist."""
    high_issues = [
        issue for issue in issues if (issue.severity or "").upper() in {"HIGH", "URGENT"}
    ]
    cycle_count = len(cycle_paths)
    if not cycle_count and not high_issues:
        return

    recipients = set()
    if project.pm_id:
        recipients.add(project.pm_id)
    for issue in high_issues:
        if issue.task_id:
            task = task_map.get(issue.task_id)
            if task and task.owner_id:
                recipients.add(task.owner_id)

    if not recipients:
        return

    window_start = datetime.utcnow() - timedelta(hours=6)
    summary_parts = []
    if cycle_count:
        summary_parts.append(f"{cycle_count} 个循环依赖")
    if high_issues:
        summary_parts.append(f"{len(high_issues)} 个高危依赖问题")
    summary = "，".join(summary_parts)

    created = False
    for user_id in recipients:
        existing = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.notification_type == "DEPENDENCY_ALERT",
                Notification.source_type == "project",
                Notification.source_id == project.id,
                Notification.created_at >= window_start,
            )
            .first()
        )
        if existing:
            continue

        create_notification(
            db=db,
            user_id=user_id,
            notification_type="DEPENDENCY_ALERT",
            title=f"项目「{project.project_name}」依赖风险提醒",
            content=f"{summary}，请前往进度看板处理相关任务。",
            source_type="project",
            source_id=project.id,
            link_url=f"/projects/{project.id}/progress-board",
            priority="URGENT" if cycle_count else "HIGH",
            extra_data={
                "cycle_count": cycle_count,
                "high_issue_count": len(high_issues),
            },
        )
        created = True

    if created:
        db.commit()
