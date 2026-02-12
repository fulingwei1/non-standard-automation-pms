# -*- coding: utf-8 -*-
"""
审批通知服务（使用统一NotificationDispatcher）
提供统一的通知发送入口和站内通知保存功能

BACKWARD COMPATIBILITY: 此模块现在通过 NotificationDispatcher 进行通知发送
"""

import logging
from typing import Any, Dict

from app.services.notification_dispatcher import NotificationDispatcher
from app.services.channel_handlers.base import (
    NotificationRequest,
    NotificationPriority,
)

logger = logging.getLogger(__name__)


class SendNotificationMixin:
    """发送通知 Mixin（使用统一通知服务）"""

    def _get_dispatcher(self):
        """获取通知调度器实例"""
        if not hasattr(self, '_notification_dispatcher') or self._notification_dispatcher is None:
            self._notification_dispatcher = NotificationDispatcher(self.db)
        return self._notification_dispatcher

    def _map_notification_type(self, approval_type: str) -> str:
        """映射审批通知类型到统一服务通知类型"""
        type_mapping = {
            "APPROVAL_PENDING": "APPROVAL_PENDING",
            "APPROVAL_APPROVED": "APPROVAL_RESULT",
            "APPROVAL_REJECTED": "APPROVAL_RESULT",
            "APPROVAL_CC": "APPROVAL_CC",
            "APPROVAL_TIMEOUT_WARNING": "APPROVAL_PENDING",
            "APPROVAL_REMIND": "APPROVAL_PENDING",
            "APPROVAL_WITHDRAWN": "APPROVAL_RESULT",
            "APPROVAL_TRANSFERRED": "APPROVAL_PENDING",
            "APPROVAL_DELEGATED": "APPROVAL_PENDING",
            "APPROVAL_ADD_APPROVER": "APPROVAL_PENDING",
            "APPROVAL_COMMENT_MENTION": "APPROVAL_PENDING",
        }
        return type_mapping.get(approval_type, "APPROVAL_PENDING")

    def _map_urgency_to_priority(self, urgency: str) -> str:
        """映射紧急程度到统一服务优先级"""
        urgency_upper = urgency.upper() if urgency else "NORMAL"
        mapping = {
            "URGENT": NotificationPriority.URGENT,
            "HIGH": NotificationPriority.HIGH,
            "NORMAL": NotificationPriority.NORMAL,
            "LOW": NotificationPriority.LOW,
        }
        return mapping.get(urgency_upper, NotificationPriority.NORMAL)

    def _send_notification(self, notification: Dict[str, Any]):
        """
        发送通知（使用统一通知服务）

        统一通知出口，支持：
        - 站内消息
        - 邮件
        - 企业微信
        - 飞书
        - 短信
        - 推送

        注意：统一服务内部已经处理了去重、用户偏好、免打扰等功能
        """
        receiver_id = notification.get("receiver_id")
        if not receiver_id:
            logger.warning("通知缺少 receiver_id，跳过发送")
            return

        # 获取通知调度器
        dispatcher = self._get_dispatcher()

        # 构建通知请求
        request = NotificationRequest(
            recipient_id=receiver_id,
            notification_type=self._map_notification_type(notification.get("type", "APPROVAL_PENDING")),
            category="approval",
            title=notification.get("title", "审批通知"),
            content=notification.get("content", ""),
            priority=self._map_urgency_to_priority(notification.get("urgency", "NORMAL")),
            source_type="approval",
            source_id=notification.get("instance_id"),
            link_url=f"/approvals/{notification.get('instance_id')}" if notification.get("instance_id") else None,
            extra_data={
                "original_type": notification.get("type"),
                "task_id": notification.get("task_id"),
                "instance_id": notification.get("instance_id"),
            },
        )

        # 使用统一服务发送通知
        # 统一服务内部会处理：
        # - 去重检查
        # - 用户偏好检查
        # - 免打扰时间检查
        # - 多渠道路由
        try:
            result = dispatcher.send_notification_request(request)
            if result.get("success"):
                logger.info(
                    f"审批通知已发送: type={notification.get('type')}, receiver={receiver_id}, "
                    f"channels={result.get('channels_sent', [])}"
                )
            else:
                logger.warning(
                    f"审批通知发送失败: type={notification.get('type')}, receiver={receiver_id}, "
                    f"reason={result.get('message', 'Unknown error')}"
                )
        except Exception as e:
            logger.error(f"发送审批通知异常: {e}", exc_info=True)
