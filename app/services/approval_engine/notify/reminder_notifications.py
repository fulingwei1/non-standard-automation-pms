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

    def notify_timeout_warning(
        self,
        task: ApprovalTask,
        hours_remaining: int,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知即将超时

        Args:
            task: 审批任务
            hours_remaining: 剩余小时数
            extra_context: 额外上下文信息
        """
        instance = task.instance
        notification = {
            "type": "APPROVAL_TIMEOUT_WARNING",
            "title": f"审批即将超时: {instance.title}",
            "content": f"您有一条审批将在{hours_remaining}小时后超时，请尽快处理",
            "receiver_id": task.assignee_id,
            "instance_id": instance.id,
            "task_id": task.id,
            "urgency": "URGENT",
            "created_at": datetime.now().isoformat(),
        }

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
