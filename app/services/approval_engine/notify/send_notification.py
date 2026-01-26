# -*- coding: utf-8 -*-
"""
审批通知服务（使用统一NotificationService）
提供统一的通知发送入口和站内通知保存功能

BACKWARD COMPATIBILITY: 此模块现在使用unified_notification_service进行通知发送
"""

import logging
from typing import Any, Dict


from app.models.notification import Notification

logger = logging.getLogger(__name__)

# 导入统一通知服务


class SendNotificationMixin:
    """发送通知 Mixin"""

    def _send_notification(self, notification: Dict[str, Any]):
        """
        发送通知

        统一通知出口，支持：
        - 站内消息
        - 邮件
        - 企业微信
        - 飞书
        - 短信
        - 推送
        """
        receiver_id = notification.get("receiver_id")
        if not receiver_id:
            logger.warning("通知缺少 receiver_id，跳过发送")
            return

        # 1. 通知去重检查
        dedup_key = self._generate_dedup_key(notification)
        if self._is_duplicate(dedup_key):
            logger.debug(f"重复通知已跳过: {notification.get('type')}")
            return

        # 2. 检查用户偏好
        prefs = self._check_user_preferences(receiver_id, notification.get("type", ""))

        # 3. 发送站内通知
        if prefs.get("system_enabled", True):
            try:
                self._save_system_notification(notification)
            except Exception as e:
                logger.error(f"保存站内通知失败: {e}")

        # 4. 发送其他渠道通知（异步）
        # 注：实际生产环境建议使用 Celery 异步任务
        if prefs.get("email_enabled"):
            self._queue_email_notification(notification)

        if prefs.get("wechat_enabled"):
            self._queue_wechat_notification(notification)

        logger.info(
            f"审批通知已发送: type={notification.get('type')}, receiver={receiver_id}"
        )

    def _save_system_notification(self, notification: Dict[str, Any]):
        """保存站内通知到数据库"""
        try:
            # 映射通知类型
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

            # 映射优先级
            urgency = notification.get("urgency", "NORMAL")
            priority_mapping = {
                "LOW": "LOW",
                "NORMAL": "NORMAL",
                "HIGH": "HIGH",
                "URGENT": "URGENT",
            }

            db_notification = Notification(
                user_id=notification["receiver_id"],
                notification_type=type_mapping.get(
                    notification.get("type"), "APPROVAL_PENDING"
                ),
                source_type="approval",
                source_id=notification.get("instance_id"),
                title=notification.get("title", "审批通知"),
                content=notification.get("content", ""),
                link_url=f"/approvals/{notification.get('instance_id')}",
                priority=priority_mapping.get(urgency, "NORMAL"),
                extra_data={
                    "original_type": notification.get("type"),
                    "task_id": notification.get("task_id"),
                    "instance_id": notification.get("instance_id"),
                },
            )

            self.db.add(db_notification)
            self.db.commit()

        except Exception as e:
            logger.error(f"保存站内通知异常: {e}")
            self.db.rollback()
            raise
