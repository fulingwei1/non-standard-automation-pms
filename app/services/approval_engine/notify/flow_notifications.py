# -*- coding: utf-8 -*-
"""
审批通知服务 - 流程变更通知

提供撤回、转审、代理、加签等流程变更通知功能
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.approval import ApprovalInstance, ApprovalTask

class FlowNotificationsMixin:
    """流程变更通知 Mixin"""

    def notify_withdrawn(
        self,
        instance: ApprovalInstance,
        affected_user_ids: List[int],
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知审批已撤回

        Args:
            instance: 审批实例
            affected_user_ids: 受影响的用户ID列表
            extra_context: 额外上下文信息
        """
        for user_id in affected_user_ids:
            notification = {
                "type": "APPROVAL_WITHDRAWN",
                "title": f"审批已撤回: {instance.title}",
                "content": f"审批「{instance.title}」已被发起人撤回",
                "receiver_id": user_id,
                "instance_id": instance.id,
                "created_at": datetime.now().isoformat(),
            }

            self._send_notification(notification)

    def notify_transferred(
        self,
        task: ApprovalTask,
        from_user_id: int,
        from_user_name: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知转审

        Args:
            task: 审批任务（已转给新审批人）
            from_user_id: 原审批人ID
            from_user_name: 原审批人姓名
            extra_context: 额外上下文信息
        """
        instance = task.instance
        content = f"您收到一条转审的审批「{instance.title}」"
        if from_user_name:
            content += f"，由{from_user_name}转交给您处理"

        notification = {
            "type": "APPROVAL_TRANSFERRED",
            "title": f"转审通知: {instance.title}",
            "content": content,
            "receiver_id": task.assignee_id,
            "instance_id": instance.id,
            "task_id": task.id,
            "urgency": instance.urgency,
            "created_at": datetime.now().isoformat(),
        }

        self._send_notification(notification)

    def notify_delegated(
        self,
        task: ApprovalTask,
        original_user_name: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知代理审批

        Args:
            task: 审批任务（已转给代理人）
            original_user_name: 原审批人姓名
            extra_context: 额外上下文信息
        """
        instance = task.instance
        content = f"您代理了一条审批「{instance.title}」"
        if original_user_name:
            content += f"（原审批人: {original_user_name}）"

        notification = {
            "type": "APPROVAL_DELEGATED",
            "title": f"代理审批通知: {instance.title}",
            "content": content,
            "receiver_id": task.assignee_id,
            "instance_id": instance.id,
            "task_id": task.id,
            "urgency": instance.urgency,
            "created_at": datetime.now().isoformat(),
        }

        self._send_notification(notification)

    def notify_add_approver(
        self,
        task: ApprovalTask,
        added_by_name: Optional[str] = None,
        position: str = "AFTER",
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知加签

        Args:
            task: 新创建的审批任务
            added_by_name: 加签操作人姓名
            position: 加签位置（BEFORE/AFTER）
            extra_context: 额外上下文信息
        """
        instance = task.instance
        position_text = "前加签" if position == "BEFORE" else "后加签"
        content = f"您被添加为审批人（{position_text}）: {instance.title}"
        if added_by_name:
            content += f"，由{added_by_name}添加"

        notification = {
            "type": "APPROVAL_ADD_APPROVER",
            "title": f"加签通知: {instance.title}",
            "content": content,
            "receiver_id": task.assignee_id,
            "instance_id": instance.id,
            "task_id": task.id,
            "urgency": instance.urgency,
            "created_at": datetime.now().isoformat(),
        }

        self._send_notification(notification)
