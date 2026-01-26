# -*- coding: utf-8 -*-
"""
审批通知服务 - 基础通知

提供主要审批流程通知功能（待审批、通过、驳回、抄送）
"""

from typing import Any, Dict, Optional

from app.models.approval import ApprovalCarbonCopy, ApprovalInstance, ApprovalTask

class BasicNotificationsMixin:
    """基础通知 Mixin"""

    def notify_pending(
        self,
        task: ApprovalTask,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知待审批

        Args:
            task: 审批任务
            extra_context: 额外上下文信息
        """
        instance = task.instance
        notification = {
            "type": "APPROVAL_PENDING",
            "title": f"您有新的审批待处理: {instance.title}",
            "content": instance.summary or "",
            "receiver_id": task.assignee_id,
            "instance_id": instance.id,
            "task_id": task.id,
            "urgency": instance.urgency,
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
        }

        self._send_notification(notification)

    def notify_approved(
        self,
        instance: ApprovalInstance,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知审批通过

        Args:
            instance: 审批实例
            extra_context: 额外上下文信息
        """
        notification = {
            "type": "APPROVAL_APPROVED",
            "title": f"审批已通过: {instance.title}",
            "content": f"您发起的审批「{instance.title}」已通过",
            "receiver_id": instance.initiator_id,
            "instance_id": instance.id,
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
        }

        self._send_notification(notification)

    def notify_rejected(
        self,
        instance: ApprovalInstance,
        rejector_name: Optional[str] = None,
        reject_comment: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知审批驳回

        Args:
            instance: 审批实例
            rejector_name: 驳回人姓名
            reject_comment: 驳回原因
            extra_context: 额外上下文信息
        """
        content = f"您发起的审批「{instance.title}」已被驳回"
        if rejector_name:
            content += f"（驳回人: {rejector_name}）"
        if reject_comment:
            content += f"\n驳回原因: {reject_comment}"

        notification = {
            "type": "APPROVAL_REJECTED",
            "title": f"审批已驳回: {instance.title}",
            "content": content,
            "receiver_id": instance.initiator_id,
            "instance_id": instance.id,
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
        }

        self._send_notification(notification)

    def notify_cc(
        self,
        cc_record: ApprovalCarbonCopy,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知抄送

        Args:
            cc_record: 抄送记录
            extra_context: 额外上下文信息
        """
        instance = cc_record.instance
        notification = {
            "type": "APPROVAL_CC",
            "title": f"您收到一条审批抄送: {instance.title}",
            "content": instance.summary or "",
            "receiver_id": cc_record.cc_user_id,
            "instance_id": instance.id,
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
        }

        self._send_notification(notification)
