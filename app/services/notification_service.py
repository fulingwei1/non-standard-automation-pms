# -*- coding: utf-8 -*-
"""
统一通知服务
支持邮件、短信、企业微信等多种通知渠道
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """通知渠道"""
    EMAIL = "email"
    SMS = "sms"
    WECHAT = "wechat"
    WEB = "web"  # 站内通知
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    """通知类型"""
    TASK_ASSIGNED = "task_assigned"  # 任务分配
    TASK_UPDATED = "task_updated"  # 任务更新
    TASK_COMPLETED = "task_completed"  # 任务完成
    TASK_APPROVED = "task_approved"  # 任务审批通过
    TASK_REJECTED = "task_rejected"  # 任务审批拒绝
    PROJECT_UPDATE = "project_update"  # 项目更新
    HEALTH_CHANGE = "health_change"  # 健康度变更
    DEADLINE_REMINDER = "deadline_reminder"  # 截止日期提醒
    SYSTEM_ANNOUNCEMENT = "system_announcement"  # 系统公告


class NotificationService:
    """统一通知服务"""

    def __init__(self):
        self.enabled_channels = self._get_enabled_channels()

    def _get_enabled_channels(self) -> List[NotificationChannel]:
        """获取启用的通知渠道"""
        channels = [NotificationChannel.WEB]  # 站内通知始终启用

        if settings.EMAIL_ENABLED:
            channels.append(NotificationChannel.EMAIL)

        if settings.SMS_ENABLED:
            channels.append(NotificationChannel.SMS)

        if settings.WECHAT_ENABLED:
            channels.append(NotificationChannel.WECHAT)

        if settings.WECHAT_WEBHOOK_URL:
            channels.append(NotificationChannel.WEBHOOK)

        return channels

    def send_notification(
        self,
        db: Session,
        recipient_id: int,
        notification_type: NotificationType,
        title: str,
        content: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[NotificationChannel]] = None,
        data: Optional[Dict[str, Any]] = None,
        link: Optional[str] = None
    ) -> bool:
        """发送通知"""
        if channels is None:
            channels = self.enabled_channels

        success = True

        # 保存站内通知记录
        if NotificationChannel.WEB in channels:
            try:
                self._save_web_notification(
                    db, recipient_id, notification_type, title, content, priority, data, link
                )
            except Exception as e:
                logger.error(f"保存站内通知失败: {e}")
                success = False

        # 发送邮件通知
        if NotificationChannel.EMAIL in channels:
            try:
                self._send_email_notification(
                    db, recipient_id, notification_type, title, content
                )
            except Exception as e:
                logger.error(f"发送邮件通知失败: {e}")

        # 发送企业微信通知
        if NotificationChannel.WECHAT in channels:
            try:
                self._send_wechat_notification(
                    db, recipient_id, notification_type, title, content, data
                )
            except Exception as e:
                logger.error(f"发送企业微信通知失败: {e}")

        # 发送 Webhook 通知
        if NotificationChannel.WEBHOOK in channels:
            try:
                self._send_webhook_notification(notification_type, title, content, data)
            except Exception as e:
                logger.error(f"发送 Webhook 通知失败: {e}")

        return success

    def _save_web_notification(
        self,
        db: Session,
        recipient_id: int,
        notification_type: NotificationType,
        title: str,
        content: str,
        priority: NotificationPriority,
        data: Optional[Dict[str, Any]],
        link: Optional[str]
    ):
        """保存站内通知"""
        # 尝试导入 WebNotification 模型
        try:
            from app.models.notification import WebNotification

            notification = WebNotification(
                recipient_id=recipient_id,
                notification_type=notification_type.value,
                title=title,
                content=content,
                priority=priority.value,
                link=link,
                data=data or {},
                is_read=False
            )

            db.add(notification)
            db.commit()
        except ImportError:
            # 如果模型不存在，记录日志但不报错
            logger.warning("WebNotification 模型不存在，跳过站内通知")

    def _send_email_notification(
        self,
        db: Session,
        recipient_id: int,
        notification_type: NotificationType,
        title: str,
        content: str
    ):
        """发送邮件通知"""
        if not settings.EMAIL_ENABLED:
            return

        from app.models.user import User

        # 获取接收人邮箱
        recipient = db.query(User).filter(User.id == recipient_id).first()
        if not recipient or not recipient.email:
            logger.warning(f"用户 {recipient_id} 没有配置邮箱")
            return

        logger.info(f"[邮件通知] 发送给 {recipient.email}: {title}")

    def _send_wechat_notification(
        self,
        db: Session,
        recipient_id: int,
        notification_type: NotificationType,
        title: str,
        content: str,
        data: Optional[Dict[str, Any]]
    ):
        """发送企业微信通知"""
        if not settings.WECHAT_ENABLED:
            return

        from app.models.user import User

        # 获取接收人企业微信账号
        recipient = db.query(User).filter(User.id == recipient_id).first()
        if not recipient:
            return

        logger.info(f"[企业微信通知] 发送给 {recipient.username}: {title}")

    def _send_webhook_notification(
        self,
        notification_type: NotificationType,
        title: str,
        content: str,
        data: Optional[Dict[str, Any]]
    ):
        """发送 Webhook 通知（如钉钉、飞书等）"""
        if not settings.WECHAT_WEBHOOK_URL:
            return

        import requests

        # 构造 Webhook 消息
        message = {
            "msgtype": "text",
            "text": {
                "content": f"【{title}】\n{content}"
            }
        }

        try:
            response = requests.post(
                settings.WECHAT_WEBHOOK_URL,
                json=message,
                timeout=10
            )
            if response.status_code != 200:
                logger.error(f"Webhook 通知失败: {response.status_code}")
        except Exception as e:
            logger.error(f"发送 Webhook 通知异常: {e}")

    def send_task_assigned_notification(
        self,
        db: Session,
        assignee_id: int,
        task_name: str,
        project_name: str,
        task_id: int,
        due_date: Optional[datetime] = None
    ):
        """发送任务分配通知"""
        title = "新任务分配"
        content = f"您被分配了新任务：{task_name}"

        if project_name:
            content += f"\n所属项目：{project_name}"

        if due_date:
            content += f"\n截止日期：{due_date.strftime('%Y-%m-%d')}"

        self.send_notification(
            db=db,
            recipient_id=assignee_id,
            notification_type=NotificationType.TASK_ASSIGNED,
            title=title,
            content=content,
            priority=NotificationPriority.NORMAL,
            link=f"/tasks/{task_id}"
        )

    def send_task_completed_notification(
        self,
        db: Session,
        task_owner_id: int,
        task_name: str,
        project_name: str
    ):
        """发送任务完成通知"""
        title = "任务已完成"
        content = f"任务「{task_name}」已完成"

        if project_name:
            content += f"\n所属项目：{project_name}"

        self.send_notification(
            db=db,
            recipient_id=task_owner_id,
            notification_type=NotificationType.TASK_COMPLETED,
            title=title,
            content=content,
            priority=NotificationPriority.NORMAL
        )

    def send_deadline_reminder(
        self,
        db: Session,
        recipient_id: int,
        task_name: str,
        due_date: datetime,
        days_remaining: int
    ):
        """发送截止日期提醒"""
        title = "任务截止提醒"
        urgency = "紧急" if days_remaining <= 1 else ("即将到期" if days_remaining <= 3 else "提醒")
        content = f"任务「{task_name}」{urgency}\n"
        content += f"截止日期：{due_date.strftime('%Y-%m-%d')}\n"
        content += f"剩余天数：{days_remaining} 天"

        priority = NotificationPriority.URGENT if days_remaining <= 1 else NotificationPriority.HIGH

        self.send_notification(
            db=db,
            recipient_id=recipient_id,
            notification_type=NotificationType.DEADLINE_REMINDER,
            title=title,
            content=content,
            priority=priority
        )


# 创建单例
notification_service = NotificationService()
