# -*- coding: utf-8 -*-
"""
项目时间线服务
"""

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.progress import Task
from app.models.project import (
    Project,
    ProjectCost,
    ProjectDocument,
    ProjectMilestone,
    ProjectStatusLog,
)
from app.schemas.project import TimelineEvent


def collect_status_change_events(
    db: Session,
    project_id: int
) -> List[TimelineEvent]:
    """
    收集状态变更事件

    Returns:
        List[TimelineEvent]: 事件列表
    """
    events = []

    status_logs = db.query(ProjectStatusLog).filter(
        ProjectStatusLog.project_id == project_id
    ).all()

    for log in status_logs:
        event = TimelineEvent(
            event_type=log.change_type or "STATUS_CHANGE",
            event_time=log.changed_at or datetime.now(),
            title=f"状态变更: {log.change_type}",
            description=f"{log.old_stage or ''} → {log.new_stage or ''}, {log.old_status or ''} → {log.new_status or ''}",
            user_name=log.changer.username if log.changer else None,
            related_id=log.id,
            related_type="status_log",
        )
        events.append(event)

    return events


def collect_milestone_events(
    db: Session,
    project_id: int
) -> List[TimelineEvent]:
    """
    收集里程碑事件

    Returns:
        List[TimelineEvent]: 事件列表
    """
    events = []

    milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id
    ).all()

    for milestone in milestones:
        # 里程碑创建
        if milestone.created_at:
            event = TimelineEvent(
                event_type="MILESTONE_CREATED",
                event_time=milestone.created_at,
                title=f"创建里程碑: {milestone.milestone_name}",
                description=f"计划日期: {milestone.planned_date.isoformat() if milestone.planned_date else '未设置'}",
                related_id=milestone.id,
                related_type="milestone",
            )
            events.append(event)

        # 里程碑完成
        if milestone.status == "COMPLETED" and milestone.actual_date:
            event = TimelineEvent(
                event_type="MILESTONE_COMPLETED",
                event_time=milestone.actual_date,
                title=f"里程碑完成: {milestone.milestone_name}",
                description=f"实际完成日期: {milestone.actual_date.isoformat()}",
                related_id=milestone.id,
                related_type="milestone",
            )
            events.append(event)

    return events


def collect_task_events(
    db: Session,
    project_id: int
) -> List[TimelineEvent]:
    """
    收集任务事件

    Returns:
        List[TimelineEvent]: 事件列表
    """
    events = []

    tasks = db.query(Task).filter(Task.project_id == project_id).all()

    for task in tasks:
        # 任务创建
        if task.created_at:
            event = TimelineEvent(
                event_type="TASK_CREATED",
                event_time=task.created_at,
                title=f"创建任务: {task.task_name}",
                description=f"负责人: {task.owner_name or '未分配'}",
                related_id=task.id,
                related_type="task",
            )
            events.append(event)

        # 任务完成
        if task.status == "COMPLETED" and task.actual_end:
            event = TimelineEvent(
                event_type="TASK_COMPLETED",
                event_time=task.actual_end,
                title=f"任务完成: {task.task_name}",
                description=f"完成进度: {task.progress_pct}%",
                related_id=task.id,
                related_type="task",
            )
            events.append(event)

    return events


def collect_cost_events(
    db: Session,
    project_id: int
) -> List[TimelineEvent]:
    """
    收集成本记录事件

    Returns:
        List[TimelineEvent]: 事件列表
    """
    events = []

    costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()

    for cost in costs:
        if cost.created_at:
            event = TimelineEvent(
                event_type="COST_RECORDED",
                event_time=cost.created_at,
                title=f"成本记录: {cost.cost_name or cost.cost_type}",
                description=f"金额: {cost.cost_amount}元, 类型: {cost.cost_type}",
                related_id=cost.id,
                related_type="cost",
            )
            events.append(event)

    return events


def collect_document_events(
    db: Session,
    project_id: int
) -> List[TimelineEvent]:
    """
    收集文档上传事件

    Returns:
        List[TimelineEvent]: 事件列表
    """
    events = []

    documents = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).all()

    for doc in documents:
        if doc.created_at:
            event = TimelineEvent(
                event_type="DOCUMENT_UPLOADED",
                event_time=doc.created_at,
                title=f"上传文档: {doc.doc_name}",
                description=f"类型: {doc.doc_type}, 分类: {doc.doc_category}",
                related_id=doc.id,
                related_type="document",
            )
            events.append(event)

    return events


def add_project_created_event(project: Project) -> TimelineEvent:
    """
    添加项目创建事件

    Returns:
        TimelineEvent: 项目创建事件
    """
    return TimelineEvent(
        event_type="PROJECT_CREATED",
        event_time=project.created_at,
        title="项目创建",
        description=f"项目编码: {project.project_code}",
        related_id=project.id,
        related_type="project",
    )
