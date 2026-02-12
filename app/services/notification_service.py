# -*- coding: utf-8 -*-
"""
统一通知服务（兼容层）
支持邮件、短信、企业微信等多种通知渠道

通知系统架构：
- app.services.unified_notification_service: 主通知服务，提供 NotificationService 和 get_notification_service()
- app.services.notification_service (本模块): 兼容层，re-export 统一服务并提供旧接口的枚举和 AlertNotificationService
- app.services.notification_dispatcher: 预警通知调度协调器，内部使用统一服务
- app.services.notification_queue: Redis 通知队列（异步分发）
- app.services.notification_utils: 通知工具函数（渠道解析、接收者解析、免打扰判断等）
- app.services.channel_handlers/: 渠道处理器（System/Email/WeChat/SMS/Webhook）

新代码推荐直接使用：
 from app.services.unified_notification_service import get_notification_service
 或
 from app.services.unified_notification_service import NotificationService

DEPRECATED: 此文件作为向后兼容层，内部使用 unified_notification_service。
新代码应直接使用 unified_notification_service。
"""

import logging
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from app.models.alert import Alert, AlertNotification

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notification import Notification as WebNotification  # noqa: F401
from app.services.unified_notification_service import get_notification_service
from app.services.channel_handlers.base import (
    NotificationRequest,
    NotificationChannel as UnifiedNotificationChannel,
)

from app.models.user import User

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """通知渠道（向后兼容）"""

    SYSTEM = "system"  # 站内通知
    EMAIL = "email"
    SMS = "sms"
    WECHAT = "wechat"
    WEB = "web"  # 站内通知（别名，向后兼容）
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """通知优先级（向后兼容）"""

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
    """统一通知服务（兼容层）
    
    DEPRECATED: 此类的实现已迁移到 unified_notification_service。
    保留此类仅用于向后兼容，内部调用统一服务。
    """

    def __init__(self, db: Optional[Session] = None):
        """初始化通知服务
        
        Args:
            db: 数据库会话（可选，用于向后兼容）
        """
        self._db = db
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

    def _map_old_channel_to_new(self, channel: NotificationChannel) -> str:
        """映射旧渠道枚举到新渠道字符串"""
        mapping = {
            NotificationChannel.WEB: UnifiedNotificationChannel.SYSTEM,
            NotificationChannel.EMAIL: UnifiedNotificationChannel.EMAIL,
            NotificationChannel.WECHAT: UnifiedNotificationChannel.WECHAT,
            NotificationChannel.SMS: UnifiedNotificationChannel.SMS,
            NotificationChannel.WEBHOOK: UnifiedNotificationChannel.WEBHOOK,
        }
        return mapping.get(channel, UnifiedNotificationChannel.SYSTEM)

    def _map_old_priority_to_new(self, priority: NotificationPriority) -> str:
        """映射旧优先级枚举到新优先级字符串"""
        if isinstance(priority, Enum):
            return priority.value
        elif isinstance(priority, str):
            return priority
        else:
            return str(priority)

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
        link: Optional[str] = None,
    ) -> bool:
        """发送通知（兼容方法，内部使用统一服务）"""
        if not db:
            logger.error("send_notification requires db parameter")
            return False

        # 使用统一服务
        unified_service = get_notification_service(db)
        
        # 映射渠道
        unified_channels = None
        if channels:
            unified_channels = [self._map_old_channel_to_new(ch) for ch in channels]
        
        # 构建通知请求
        request = NotificationRequest(
            recipient_id=recipient_id,
            notification_type=notification_type.value if isinstance(notification_type, Enum) else str(notification_type),
            category=self._infer_category(notification_type),
            title=title,
            content=content,
            priority=self._map_old_priority_to_new(priority),
            channels=unified_channels,
            source_type=None,
            source_id=None,
            link_url=link,
            extra_data=data,
        )
        
        # 发送通知
        result = unified_service.send_notification(request)
        return result.get("success", False)

    def _infer_category(self, notification_type: NotificationType) -> str:
        """从通知类型推断分类"""
        type_str = notification_type.value if isinstance(notification_type, Enum) else str(notification_type)
        if "task" in type_str.lower():
            return "task"
        elif "approval" in type_str.lower():
            return "approval"
        elif "alert" in type_str.lower():
            return "alert"
        elif "ecn" in type_str.lower():
            return "ecn"
        elif "project" in type_str.lower():
            return "project"
        else:
            return "general"

    # 旧的实现方法已移除，现在通过统一服务处理

    def send_task_assigned_notification(
        self,
        db: Session,
        assignee_id: int,
        task_name: str,
        project_name: str,
        task_id: int,
        due_date: Optional[datetime] = None,
    ):
        """发送任务分配通知（兼容方法）"""
        title = f"新任务分配：{task_name}"
        content = f"您有新的任务「{task_name}」（项目：{project_name}）"
        if due_date:
            content += f"，截止日期：{due_date.strftime('%Y-%m-%d')}"
        return self.send_notification(
            db=db,
            recipient_id=assignee_id,
            notification_type=NotificationType.TASK_ASSIGNED,
            title=title,
            content=content,
            data={"task_id": task_id, "project_name": project_name},
        )

    def send_task_completed_notification(
        self, db: Session, task_owner_id: int, task_name: str, project_name: str
    ):
        """发送任务完成通知（兼容方法）"""
        title = f"任务已完成：{task_name}"
        content = f"任务「{task_name}」（项目：{project_name}）已完成"
        return self.send_notification(
            db=db,
            recipient_id=task_owner_id,
            notification_type=NotificationType.TASK_COMPLETED,
            title=title,
            content=content,
        )

    def send_deadline_reminder(
        self,
        db: Session,
        recipient_id: int,
        task_name: str,
        due_date: datetime,
        days_remaining: int,
    ):
        """发送截止日期提醒（兼容方法）"""
        if days_remaining <= 1:
            title = f"紧急：任务「{task_name}」即将到期"
            content = f"紧急提醒：任务「{task_name}」将于 {due_date.strftime('%Y-%m-%d')} 到期，仅剩 {days_remaining} 天"
        else:
            title = f"提醒：任务「{task_name}」即将到期"
            content = f"任务「{task_name}」将于 {due_date.strftime('%Y-%m-%d')} 到期，剩余 {days_remaining} 天"
        return self.send_notification(
            db=db,
            recipient_id=recipient_id,
            notification_type=NotificationType.DEADLINE_REMINDER,
            title=title,
            content=content,
        )


# 创建单例（向后兼容）
def get_notification_service_instance(db: Optional[Session] = None) -> NotificationService:
    """获取通知服务实例（向后兼容）"""
    return NotificationService(db)

notification_service = NotificationService()


class AlertNotificationService:
    """预警通知服务（使用统一的NotificationService）"""

    def __init__(self, db: Session):
        self.db = db
        self.unified_service = get_notification_service(db)

    @staticmethod
    def create_alert_notification(
        db: Session, alert: "Alert", notify_channel: str, status: str = "pending"
    ) -> "AlertNotification":
        """创建预警通知记录（向后兼容）"""
        from app.models.alert import AlertNotification as AlertNotificationModel
        from app.models.alert import AlertRecord
        
        # 如果 alert 是 AlertRecord，直接使用
        if isinstance(alert, AlertRecord):
            notification = AlertNotificationModel(
                alert_id=alert.id,
                notify_user_id=alert.assignee_id,
                notify_channel=notify_channel,
                status=status,
            )
        else:
            # 兼容其他类型的 alert
            notification = AlertNotificationModel(
                alert_id=getattr(alert, 'id', 0),
                notify_user_id=getattr(alert, 'assignee_id', None),
                notify_channel=notify_channel,
                status=status,
            )
        db.add(notification)
        db.commit()
        return notification

    def send_alert_notification(
        self,
        alert: "Alert",
        user: Optional["User"] = None,
        user_ids: Optional[List[int]] = None,
        channels: Optional[List[str]] = None,
        force_send: bool = False,
    ) -> bool:
        """发送预警通知"""
        try:
            from app.models.alert import AlertRecord

            # 确定接收者
            recipients: List[int] = []
            if user_ids:
                recipients.extend([uid for uid in user_ids if uid])
            elif user and getattr(user, "id", None):
                recipients.append(user.id)
            elif isinstance(alert, AlertRecord):
                if getattr(alert, "assignee_id", None):
                    recipients.append(alert.assignee_id)
                elif getattr(alert, "handler_id", None):
                    recipients.append(alert.handler_id)
            elif hasattr(alert, "assignee_id") and getattr(alert, "assignee_id", None):
                recipients.append(alert.assignee_id)

            if not recipients:
                logger.warning("无法确定预警通知接收者")
                return False

            # 获取预警信息
            alert_title = (
                getattr(alert, "alert_title", None)
                or getattr(alert, "title", None)
                or "预警通知"
            )
            alert_content = (
                getattr(alert, "alert_content", None)
                or getattr(alert, "description", None)
                or f"预警：{alert_title}"
            )
            normalized_channels = None
            if channels:
                channel_mapping = {
                    "SYSTEM": "SYSTEM",
                    "WEB": "SYSTEM",
                    "EMAIL": "EMAIL",
                    "WECHAT": "WECHAT",
                    "SMS": "SMS",
                    "WEBHOOK": "WEBHOOK",
                }
                normalized_channels = []
                for channel in channels:
                    if not channel:
                        continue
                    mapped = channel_mapping.get(str(channel).upper())
                    if mapped:
                        normalized_channels.append(mapped)
                if normalized_channels:
                    normalized_channels = list(dict.fromkeys(normalized_channels))
                else:
                    normalized_channels = None

            from app.services.notification_dispatcher import NotificationDispatcher

            dispatcher = NotificationDispatcher(self.db)
            result = dispatcher.dispatch_alert_notifications(
                alert=alert,
                user_ids=recipients,
                channels=normalized_channels,
                title=alert_title,
                content=alert_content,
                force_send=force_send,
            )
            return bool(result.get("queued") or result.get("sent") or result.get("created"))
        except Exception as e:
            logger.error(f"发送预警通知失败: {e}")
            return False

    def get_user_notifications(
        self,
        user_id: int,
        is_read: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """获取用户的通知列表"""
        from app.models.alert import AlertNotification
        from app.models.alert import AlertRecord
        
        try:
            query = self.db.query(AlertNotification).filter(
                AlertNotification.notify_user_id == user_id
            )
            
            if is_read is not None:
                # AlertNotification 可能没有 is_read 字段，使用 status 判断
                if is_read:
                    query = query.filter(AlertNotification.status == "SENT")
                else:
                    query = query.filter(AlertNotification.status != "SENT")
            
            total = query.count()
            notifications = query.order_by(AlertNotification.created_at.desc()).offset(offset).limit(limit).all()
            
            # 转换为字典格式
            items = []
            for notif in notifications:
                alert = self.db.query(AlertRecord).filter(AlertRecord.id == notif.alert_id).first()
                item = {
                    "id": notif.id,
                    "alert_id": notif.alert_id,
                    "alert_title": alert.alert_title if alert else notif.notify_title,
                    "alert_level": alert.alert_level if alert else "NORMAL",
                    "notify_channel": notif.notify_channel,
                    "status": notif.status,
                    "created_at": notif.created_at.isoformat() if notif.created_at else None,
                    "sent_at": notif.sent_at.isoformat() if notif.sent_at else None,
                    "is_read": notif.status == "SENT",  # 简化判断
                }
                items.append(item)
            
            return {
                "success": True,
                "items": items,
                "total": total,
            }
        except Exception as e:
            logger.error(f"获取用户通知列表失败: {e}")
            return {
                "success": False,
                "message": str(e),
                "items": [],
                "total": 0,
            }

    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """标记通知为已读"""
        from app.models.alert import AlertNotification
        
        try:
            notification = self.db.query(AlertNotification).filter(
                AlertNotification.id == notification_id,
                AlertNotification.notify_user_id == user_id
            ).first()
            
            if not notification:
                return False
            
            # 更新状态为已读（使用 status 字段）
            notification.status = "SENT"
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"标记通知已读失败: {e}")
            self.db.rollback()
            return False

    def get_unread_count(self, user_id: int) -> int:
        """获取未读通知数量"""
        from app.models.alert import AlertNotification
        
        try:
            count = self.db.query(AlertNotification).filter(
                AlertNotification.notify_user_id == user_id,
                AlertNotification.status != "SENT"  # 未发送/未读
            ).count()
            return count
        except Exception as e:
            logger.error(f"获取未读通知数量失败: {e}")
            return 0

    def batch_mark_read(self, notification_ids: List[int], user_id: int) -> Dict[str, Any]:
        """批量标记通知为已读"""
        from app.models.alert import AlertNotification
        
        try:
            notifications = self.db.query(AlertNotification).filter(
                AlertNotification.id.in_(notification_ids),
                AlertNotification.notify_user_id == user_id
            ).all()
            
            success_count = 0
            for notification in notifications:
                notification.status = "SENT"
                success_count += 1
            
            self.db.commit()
            
            return {
                "success": True,
                "success_count": success_count,
                "total_count": len(notification_ids),
            }
        except Exception as e:
            logger.error(f"批量标记通知已读失败: {e}")
            self.db.rollback()
            return {
                "success": False,
                "message": str(e),
                "success_count": 0,
                "total_count": len(notification_ids),
            }
