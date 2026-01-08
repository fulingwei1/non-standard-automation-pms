# -*- coding: utf-8 -*-
"""
预警通知服务
提供统一的预警通知发送、阅读状态管理和查询接口
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.alert import AlertRecord, AlertNotification
from app.models.user import User
from app.models.notification import Notification, NotificationSettings
from app.services.notification_dispatcher import (
    NotificationDispatcher,
    resolve_channels,
    resolve_recipients,
    resolve_channel_target,
    channel_allowed,
    is_quiet_hours,
    next_quiet_resume,
)


logger = logging.getLogger(__name__)


class AlertNotificationService:
    """预警通知服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.dispatcher = NotificationDispatcher(db)

    def send_alert_notification(
        self,
        alert: AlertRecord,
        user_ids: Optional[List[int]] = None,
        channels: Optional[List[str]] = None,
        force_send: bool = False
    ) -> Dict[str, Any]:
        """
        发送预警通知
        
        Args:
            alert: 预警记录
            user_ids: 指定用户ID列表，如果为None则从规则配置中获取
            channels: 指定通知渠道列表，如果为None则从规则配置中获取
            force_send: 是否强制发送（忽略免打扰时段）
        
        Returns:
            包含发送结果的字典
        """
        try:
            # 1. 确定通知渠道
            if channels is None:
                channels = resolve_channels(alert)
            if not channels:
                channels = ["SYSTEM"]  # 默认使用站内消息

            # 2. 确定通知对象
            if user_ids is None:
                recipients = resolve_recipients(self.db, alert)
                user_ids = list(recipients.keys())
            
            if not user_ids:
                logger.warning(f"Alert {alert.id} has no recipients, skipping notification")
                return {
                    "success": False,
                    "message": "No recipients found",
                    "notifications_created": 0
                }

            # 3. 创建通知记录
            current_time = datetime.now()
            notifications_created = 0
            notifications_sent = 0
            notifications_failed = 0
            notifications_delayed = 0

            for user_id in user_ids:
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user or not user.is_active:
                    continue

                # 获取用户通知设置
                settings = self.db.query(NotificationSettings).filter(
                    NotificationSettings.user_id == user_id
                ).first()

                for channel in channels:
                    # 检查渠道是否允许
                    if not channel_allowed(channel, settings):
                        continue

                    # 检查是否已存在通知（避免重复）
                    target = resolve_channel_target(channel, user)
                    if not target:
                        continue

                    existing = self.db.query(AlertNotification).filter(
                        AlertNotification.alert_id == alert.id,
                        AlertNotification.notify_channel == channel.upper(),
                        AlertNotification.notify_target == target
                    ).first()

                    if existing:
                        continue

                    # 创建通知记录
                    notification = AlertNotification(
                        alert_id=alert.id,
                        notify_channel=channel.upper(),
                        notify_target=target,
                        notify_user_id=user_id,
                        notify_title=alert.alert_title,
                        notify_content=alert.alert_content,
                        status='PENDING'
                    )

                    # 检查免打扰时段
                    if not force_send and is_quiet_hours(settings, current_time):
                        notification.next_retry_at = next_quiet_resume(settings, current_time)
                        notification.error_message = "Delayed due to quiet hours"
                        notification.status = 'PENDING'
                        notifications_delayed += 1
                    else:
                        # 立即尝试发送
                        try:
                            success = self.dispatcher.dispatch(notification, alert, user)
                            if success:
                                notifications_sent += 1
                            else:
                                notifications_failed += 1
                        except Exception as e:
                            logger.error(f"Failed to send notification for alert {alert.id}: {str(e)}")
                            notification.status = 'FAILED'
                            notification.error_message = str(e)
                            notifications_failed += 1

                    self.db.add(notification)
                    notifications_created += 1

            self.db.flush()

            return {
                "success": True,
                "message": "Notifications processed",
                "notifications_created": notifications_created,
                "notifications_sent": notifications_sent,
                "notifications_failed": notifications_failed,
                "notifications_delayed": notifications_delayed
            }

        except Exception as e:
            logger.error(f"Error sending alert notifications: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "notifications_created": 0
            }

    def mark_notification_read(
        self,
        notification_id: int,
        user_id: int
    ) -> bool:
        """
        标记通知为已读
        
        Args:
            notification_id: 通知ID
            user_id: 用户ID（用于权限验证）
        
        Returns:
            是否成功
        """
        try:
            notification = self.db.query(AlertNotification).filter(
                AlertNotification.id == notification_id,
                AlertNotification.notify_user_id == user_id
            ).first()

            if not notification:
                logger.warning(f"Notification {notification_id} not found or not owned by user {user_id}")
                return False

            if notification.read_at:
                # 已经标记为已读
                return True

            notification.read_at = datetime.now()
            self.db.add(notification)
            self.db.commit()

            # 同时更新站内消息的阅读状态
            if notification.notify_channel == "SYSTEM":
                system_notification = self.db.query(Notification).filter(
                    Notification.user_id == user_id,
                    Notification.source_type == "alert",
                    Notification.source_id == notification.alert_id,
                    Notification.notification_type == "ALERT_NOTIFICATION"
                ).first()
                if system_notification:
                    system_notification.is_read = True
                    system_notification.read_at = datetime.now()
                    self.db.add(system_notification)

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}", exc_info=True)
            self.db.rollback()
            return False

    def get_user_notifications(
        self,
        user_id: int,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        获取用户的通知列表
        
        Args:
            user_id: 用户ID
            is_read: 是否已读（None表示全部）
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            包含通知列表和总数的字典
        """
        try:
            query = self.db.query(AlertNotification).filter(
                AlertNotification.notify_user_id == user_id
            )

            if is_read is not None:
                if is_read:
                    query = query.filter(AlertNotification.read_at.isnot(None))
                else:
                    query = query.filter(AlertNotification.read_at.is_(None))

            total = query.count()

            notifications = query.options(
                # 预加载关联数据，避免N+1查询
            ).join(AlertRecord).order_by(
                AlertNotification.created_at.desc()
            ).offset(offset).limit(limit).all()

            # 构建返回数据
            items = []
            for notification in notifications:
                alert = notification.alert
                items.append({
                    "id": notification.id,
                    "alert_id": alert.id if alert else None,
                    "alert_no": alert.alert_no if alert else None,
                    "alert_level": alert.alert_level if alert else None,
                    "alert_title": notification.notify_title or (alert.alert_title if alert else ""),
                    "alert_content": notification.notify_content or (alert.alert_content if alert else ""),
                    "notify_channel": notification.notify_channel,
                    "status": notification.status,
                    "is_read": notification.read_at is not None,
                    "read_at": notification.read_at.isoformat() if notification.read_at else None,
                    "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
                    "created_at": notification.created_at.isoformat() if notification.created_at else None,
                    "project_id": alert.project_id if alert else None,
                    "project_name": alert.project.project_name if alert and alert.project else None,
                })

            return {
                "success": True,
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Error getting user notifications: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "items": [],
                "total": 0
            }

    def get_unread_count(self, user_id: int) -> int:
        """
        获取用户未读通知数量
        
        Args:
            user_id: 用户ID
        
        Returns:
            未读通知数量
        """
        try:
            count = self.db.query(AlertNotification).filter(
                AlertNotification.notify_user_id == user_id,
                AlertNotification.read_at.is_(None),
                AlertNotification.status == 'SENT'
            ).count()
            return count
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}", exc_info=True)
            return 0

    def batch_mark_read(
        self,
        notification_ids: List[int],
        user_id: int
    ) -> Dict[str, Any]:
        """
        批量标记通知为已读
        
        Args:
            notification_ids: 通知ID列表
            user_id: 用户ID
        
        Returns:
            包含成功和失败数量的字典
        """
        try:
            notifications = self.db.query(AlertNotification).filter(
                AlertNotification.id.in_(notification_ids),
                AlertNotification.notify_user_id == user_id,
                AlertNotification.read_at.is_(None)
            ).all()

            success_count = 0
            for notification in notifications:
                notification.read_at = datetime.now()
                self.db.add(notification)
                success_count += 1

            self.db.commit()

            return {
                "success": True,
                "total": len(notification_ids),
                "success_count": success_count,
                "failed_count": len(notification_ids) - success_count
            }

        except Exception as e:
            logger.error(f"Error batch marking notifications as read: {str(e)}", exc_info=True)
            self.db.rollback()
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "total": len(notification_ids),
                "success_count": 0,
                "failed_count": len(notification_ids)
            }


# 便捷函数
def send_alert_notification(
    db: Session,
    alert: AlertRecord,
    user_ids: Optional[List[int]] = None,
    channels: Optional[List[str]] = None,
    force_send: bool = False
) -> Dict[str, Any]:
    """
    发送预警通知的便捷函数
    
    Args:
        db: 数据库会话
        alert: 预警记录
        user_ids: 指定用户ID列表
        channels: 指定通知渠道列表
        force_send: 是否强制发送
    
    Returns:
        发送结果字典
    """
    service = AlertNotificationService(db)
    return service.send_alert_notification(alert, user_ids, channels, force_send)


def mark_notification_read(
    db: Session,
    notification_id: int,
    user_id: int
) -> bool:
    """
    标记通知为已读的便捷函数
    
    Args:
        db: 数据库会话
        notification_id: 通知ID
        user_id: 用户ID
    
    Returns:
        是否成功
    """
    service = AlertNotificationService(db)
    return service.mark_notification_read(notification_id, user_id)


def get_user_notifications(
    db: Session,
    user_id: int,
    is_read: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    获取用户通知列表的便捷函数
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        is_read: 是否已读
        limit: 返回数量限制
        offset: 偏移量
    
    Returns:
        通知列表和总数
    """
    service = AlertNotificationService(db)
    return service.get_user_notifications(user_id, is_read, limit, offset)
