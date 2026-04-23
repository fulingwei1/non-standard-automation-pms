# -*- coding: utf-8 -*-
"""
审批通知服务 - 基础通知

提供主要审批流程通知功能（待审批、通过、驳回、抄送）
"""

from typing import Any, Dict, Optional

from app.models.approval import ApprovalCarbonCopy, ApprovalInstance, ApprovalTask


class BasicNotificationsMixin:
    """基础通知 Mixin"""

    def __init__(self, db=None):
        self.db = db

    @staticmethod
    def _safe_instance_title(instance: ApprovalInstance) -> str:
        title = getattr(instance, "title", None)
        if title:
            return title
        return getattr(instance, "business_key", None) or f"审批#{getattr(instance, 'id', '')}"

    @staticmethod
    def _safe_iso(value: Any) -> Optional[str]:
        return value.isoformat() if hasattr(value, "isoformat") else None

    def notify_pending(
        self,
        instance_or_task,
        node=None,
        task: Optional[ApprovalTask] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """通知待审批，兼容新旧调用签名。"""
        if task is None and node is None:
            task = instance_or_task
            instance = task.instance
        else:
            instance = instance_or_task

        notification = {
            "type": "APPROVAL_PENDING",
            "title": f"您有新的审批待处理: {self._safe_instance_title(instance)}",
            "content": getattr(instance, "summary", "") or "",
            "receiver_id": getattr(task, "assignee_id", None),
            "instance_id": getattr(instance, "id", None),
            "task_id": getattr(task, "id", None),
            "urgency": getattr(instance, "urgency", "NORMAL"),
            "created_at": self._safe_iso(getattr(instance, "created_at", None)),
        }

        self._send_notification(notification)

    def notify_approved(
        self,
        instance: ApprovalInstance,
        node=None,
        task: Optional[ApprovalTask] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """通知审批通过，兼容新旧调用签名。"""
        title = self._safe_instance_title(instance)
        notification = {
            "type": "APPROVAL_APPROVED",
            "title": f"审批已通过: {title}",
            "content": f"您发起的审批「{title}」已通过",
            "receiver_id": getattr(instance, "initiator_id", None),
            "instance_id": getattr(instance, "id", None),
            "created_at": self._safe_iso(getattr(instance, "created_at", None)),
        }

        self._send_notification(notification)

    def notify_rejected(
        self,
        instance: ApprovalInstance,
        node=None,
        task: Optional[ApprovalTask] = None,
        rejector_name: Optional[str] = None,
        reject_comment: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """通知审批驳回，兼容新旧调用签名。"""
        if isinstance(node, str) and rejector_name is None and task is None:
            rejector_name = node
            node = None

        title = self._safe_instance_title(instance)
        content = f"您发起的审批「{title}」已被驳回"
        if rejector_name:
            content += f"（驳回人: {rejector_name}）"
        if reject_comment:
            content += f"\n驳回原因: {reject_comment}"

        notification = {
            "type": "APPROVAL_REJECTED",
            "title": f"审批已驳回: {title}",
            "content": content,
            "receiver_id": getattr(instance, "initiator_id", None),
            "instance_id": getattr(instance, "id", None),
            "created_at": self._safe_iso(getattr(instance, "created_at", None)),
        }

        self._send_notification(notification)

    def notify_cc(
        self,
        cc_or_instance,
        node=None,
        cc_user_ids=None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """通知抄送，兼容抄送记录对象和旧式(instance, node, user_ids)调用。"""
        if cc_user_ids is None and node is None:
            cc_record = cc_or_instance
            instance = cc_record.instance
            user_ids = [cc_record.cc_user_id]
        else:
            instance = cc_or_instance
            user_ids = list(cc_user_ids or [])

        title = self._safe_instance_title(instance)
        for user_id in user_ids:
            notification = {
                "type": "APPROVAL_CC",
                "title": f"您收到一条审批抄送: {title}",
                "content": getattr(instance, "summary", "") or "",
                "receiver_id": user_id,
                "instance_id": getattr(instance, "id", None),
                "created_at": self._safe_iso(getattr(instance, "created_at", None)),
            }
            self._send_notification(notification)
