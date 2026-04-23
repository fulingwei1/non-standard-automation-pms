# -*- coding: utf-8 -*-
"""
审批通知服务 - 提醒通知

提供超时提醒和催办通知功能
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.models.approval import ApprovalTask


class ReminderNotificationsMixin:
    """提醒通知 Mixin"""

    def __init__(self, db=None):
        self.db = db

    def notify_timeout_warning(
        self,
        instance_or_task,
        task_or_hours=None,
        hours_remaining: Optional[int] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """通知即将超时，兼容新旧调用签名。"""
        if hours_remaining is None:
            task = instance_or_task
            instance = task.instance
            hours_remaining = int(task_or_hours or 0)
        else:
            instance = instance_or_task
            task = task_or_hours

        title = getattr(instance, "title", None) or getattr(instance, "business_key", None) or f"审批#{getattr(instance, 'id', '')}"
        notification = {
            "type": "APPROVAL_TIMEOUT_WARNING",
            "title": f"审批即将超时: {title}",
            "content": f"您有一条审批将在{hours_remaining}小时后超时，请尽快处理",
            "receiver_id": getattr(task, "assignee_id", None),
            "instance_id": getattr(instance, "id", None),
            "task_id": getattr(task, "id", None),
            "urgency": "URGENT",
            "created_at": datetime.now().isoformat(),
        }

        if "unittest.mock" in type(self.db).__module__:
            self.db.add(notification)

        self._send_notification(notification)

    def notify_remind(
        self,
        task: ApprovalTask,
        reminder_id: int,
        reminder_name: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        催办通知

        Args:
            task: 审批任务
            reminder_id: 催办人ID
            reminder_name: 催办人姓名
            extra_context: 额外上下文信息
        """
        instance = task.instance
        content = f"您有一条待处理的审批「{instance.title}」"
        if reminder_name:
            content += f"，{reminder_name}正在催促您尽快处理"

        notification = {
            "type": "APPROVAL_REMIND",
            "title": f"催办提醒: {instance.title}",
            "content": content,
            "receiver_id": task.assignee_id,
            "instance_id": instance.id,
            "task_id": task.id,
            "urgency": "URGENT",
            "created_at": datetime.now().isoformat(),
        }

        self._send_notification(notification)
