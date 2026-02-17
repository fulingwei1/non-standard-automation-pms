# -*- coding: utf-8 -*-
"""
工程师延期报告 API 端点
包含：任务延期报告
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.alert import ExceptionEvent
from app.models.project import Project
from app.models.task_center import TaskUnified
from app.models.user import User
from app.schemas import engineer as schemas
from app.services.progress_aggregation_service import aggregate_task_progress
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tasks/{task_id}/report-delay", response_model=schemas.DelayReportResponse)
def report_task_delay(
    task_id: int,
    delay_data: schemas.DelayReportRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    报告任务延期（创建异常事件，自动通知相关方）
    """
    # 获取任务
    task = get_or_404(db, TaskUnified, task_id, "任务不存在")

    # 验证权限
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能报告自己任务的延期")

    # 更新任务延期信息
    task.is_delayed = True
    task.delay_reason = delay_data.delay_reason
    task.delay_responsibility = delay_data.delay_responsibility
    task.delay_impact_scope = delay_data.delay_impact_scope
    task.new_completion_date = delay_data.new_completion_date
    task.delay_reported_at = datetime.now()
    task.delay_reported_by = current_user.id
    task.updated_at = datetime.now()

    db.commit()

    # 创建异常事件
    exception_event = ExceptionEvent(
        event_no=f"EXC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        event_type='SCHEDULE_DELAY',
        severity='MEDIUM' if delay_data.schedule_impact_days <= 5 else 'HIGH',
        source_type='TASK_DELAY',
        source_id=task_id,
        project_id=task.project_id,
        title=f"任务延期：{task.title}",
        description=delay_data.delay_reason,
        discovered_at=datetime.now(),
        discovered_by=current_user.id,
        impact_scope=delay_data.delay_impact_scope,
        impact_description=f"延期{delay_data.schedule_impact_days}天",
        schedule_impact=delay_data.schedule_impact_days,
        cost_impact=delay_data.cost_impact,
        root_cause=delay_data.root_cause_analysis,
        preventive_measures=delay_data.preventive_measures,
        status='OPEN'
    )

    db.add(exception_event)
    db.commit()
    db.refresh(exception_event)

    # 确定可见范围和通知对象
    visible_roles = []
    notifications_count = 0

    if delay_data.delay_impact_scope == 'LOCAL':
        visible_roles = ['PROJECT_TEAM']
        notifications_count = 1
    elif delay_data.delay_impact_scope == 'PROJECT':
        visible_roles = ['PROJECT_TEAM', 'DEPT_HEAD', 'PM']
        notifications_count = 3
    elif delay_data.delay_impact_scope == 'MULTI_PROJECT':
        visible_roles = ['PROJECT_TEAM', 'DEPT_HEAD', 'PM', 'PMO', 'MANAGEMENT']
        notifications_count = 5

    # 发送异常通知
    from app.services.notification_dispatcher import NotificationDispatcher
    from app.services.channel_handlers.base import NotificationRequest, NotificationPriority
    try:
        # 通知项目经理
        project = db.query(Project).filter(Project.id == task.project_id).first()
        if project and project.pm_id:
            dispatcher = NotificationDispatcher(db)
            request = NotificationRequest(
                recipient_id=project.pm_id,
                notification_type="PROJECT_UPDATE",
                category="project",
                title=f"任务延期报告：{task.title or f'任务#{task.id}'}",
                content=f"延期天数：{delay_data.schedule_impact_days}天\n原因分析：{delay_data.root_cause_analysis or '无'}",
                priority=NotificationPriority.HIGH,
                source_type="task",
                source_id=task.id,
                link_url=f"/engineers/tasks/{task.id}",
            )
            dispatcher.send_notification_request(request)
    except Exception:
        # 通知失败不影响主流程
        logger.warning("任务延期报告通知发送失败，不影响主流程", exc_info=True)

    # 检查是否需要更新项目健康度
    aggregate_task_progress(db, task.id)

    return schemas.DelayReportResponse(
        task_id=task.id,
        exception_event_id=exception_event.id,
        delay_visible_to=visible_roles,
        notifications_sent_count=notifications_count,
        health_status_updated=True
    )
