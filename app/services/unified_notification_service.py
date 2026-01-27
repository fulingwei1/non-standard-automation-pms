# -*- coding: utf-8 -*-
"""
统一通知服务
整合所有通知渠道，提供统一接口
"""

from __future__ import annotations

import logging
from datetime import datetime
from hashlib import md5
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.alert import AlertNotification
from app.models.notification import NotificationSettings
from app.services.channel_handlers.base import (
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
    NotificationResult,
)

if TYPE_CHECKING:
    from app.models.alert import Alert


class NotificationService:
    """统一通知服务"""

    _dedup_cache: Dict[str, datetime] = {}
    _dedup_window_seconds = 300

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self._handlers = {
            NotificationChannel.SYSTEM: SystemChannelHandler(
                db, NotificationChannel.SYSTEM
            ),
            NotificationChannel.EMAIL: EmailChannelHandler(
                db, NotificationChannel.EMAIL
            ),
            NotificationChannel.WECHAT: WeChatChannelHandler(
                db, NotificationChannel.WECHAT
            ),
            NotificationChannel.SMS: SMSChannelHandler(db, NotificationChannel.SMS),
            NotificationChannel.WEBHOOK: WebhookChannelHandler(
                db, NotificationChannel.WEBHOOK
            ),
        }

    def _get_user_settings(self, user_id: int) -> Optional[NotificationSettings]:
        """获取用户通知偏好"""
        return (
            self.db.query(NotificationSettings)
            .filter(NotificationSettings.user_id == user_id)
            .first()
        )

    def _check_dedup(self, request: NotificationRequest) -> bool:
        """检查是否重复通知"""
        if request.force_send:
            return False

        dedup_key = self._dedup_key(request)
        if dedup_key in self._dedup_cache:
            time_diff = (datetime.now() - self._dedup_cache[dedup_key]).total_seconds()
            if time_diff < self._dedup_window_seconds:
                self.logger.info(f"跳过重复通知: {dedup_key}")
                return True
        return False

    def _dedup_key(self, request: NotificationRequest) -> str:
        """生成去重key"""
        content = f"{request.recipient_id}:{request.notification_type}:{request.source_type}:{request.source_id}"
        return md5(content.encode()).hexdigest()

    def _update_dedup_cache(self, request: NotificationRequest):
        """更新去重缓存"""
        if not request.force_send:
            dedup_key = self._dedup_key(request)
            self._dedup_cache[dedup_key] = datetime.now()

    def _check_quiet_hours(self, user_settings: Optional[NotificationSettings]) -> bool:
        """检查免打扰时间"""
        if (
            not user_settings
            or not user_settings.quiet_hours_start
            or not user_settings.quiet_hours_end
        ):
            return False

        try:
            start = datetime.strptime(user_settings.quiet_hours_start, "%H:%M").time()
            end = datetime.strptime(user_settings.quiet_hours_end, "%H:%M").time()
            now = datetime.now().time()

            if start <= end:
                return start <= now <= end
            return now >= start or now <= end
        except Exception as e:
            self.logger.error(f"检查免打扰时间失败: {e}")
            return False

    def _should_send_by_category(
        self,
        request: NotificationRequest,
        user_settings: Optional[NotificationSettings],
    ) -> bool:
        """根据分类检查是否应该发送"""
        if not user_settings or request.force_send:
            return True

        category_mapping = {
            "task": lambda s: s.task_notifications or False,
            "approval": lambda s: s.approval_notifications or False,
            "alert": lambda s: s.alert_notifications or False,
            "issue": lambda s: s.issue_notifications or False,
            "project": lambda s: s.project_notifications or False,
        }
        return category_mapping.get(request.category, lambda s: True)(user_settings)

    def _determine_channels(self, request: NotificationRequest) -> List[str]:
        """确定使用的通知渠道"""
        if request.channels:
            return request.channels

        channels = [NotificationChannel.SYSTEM]
        priority_level = (
            [
                NotificationPriority.URGENT,
                NotificationPriority.HIGH,
                NotificationPriority.NORMAL,
                NotificationPriority.LOW,
            ].index(request.priority)
            if request.priority
            in [
                NotificationPriority.URGENT,
                NotificationPriority.HIGH,
                NotificationPriority.NORMAL,
                NotificationPriority.LOW,
            ]
            else 1
        )

        user_settings = self._get_user_settings(request.recipient_id)
        if user_settings:
            if user_settings.wechat_enabled or priority_level <= 0:
                channels.append(NotificationChannel.WECHAT)
            if user_settings.email_enabled or priority_level <= 1:
                channels.append(NotificationChannel.EMAIL)
            if user_settings.sms_enabled or priority_level <= 0:
                channels.append(NotificationChannel.SMS)
        else:
            if priority_level <= 0:
                channels.extend([NotificationChannel.WECHAT, NotificationChannel.EMAIL])
            elif priority_level <= 1:
                channels.append(NotificationChannel.EMAIL)

        return list(set(channels))

    def _send_to_channels(
        self, request: NotificationRequest, channels: List[str]
    ) -> List[NotificationResult]:
        """发送通知到指定渠道"""
        results = []
        for channel in channels:
            if channel not in self._handlers:
                self.logger.warning(f"未注册的渠道: {channel}")
                continue
            handler = self._handlers[channel]
            try:
                result = handler.send(request)
                results.append(result)
            except Exception as e:
                self.logger.error(f"渠道{channel}发送失败: {e}")
                results.append(
                    NotificationResult(
                        channel=channel, success=False, error_message=str(e)
                    )
                )
        return results

    def send_notification(self, request: NotificationRequest) -> Dict[str, Any]:
        """发送通知（核心方法）"""
        if self._check_dedup(request):
            return {
                "success": False,
                "deduped": True,
                "channels_sent": [],
                "channels_failed": [],
                "message": "跳过重复通知",
            }

        user_settings = self._get_user_settings(request.recipient_id)

        if self._check_quiet_hours(user_settings):
            self.logger.info(f"用户{request.recipient_id}处于免打扰时间，跳过通知")
            return {
                "success": True,
                "deduped": False,
                "quiet_hours": True,
                "channels_sent": [NotificationChannel.SYSTEM],
                "channels_failed": [],
                "message": "已进入免打扰队列",
            }

        if not self._should_send_by_category(user_settings, request.category):
            self.logger.info(f"用户{request.recipient_id}禁用{request.category}通知")
            return {
                "success": True,
                "deduped": False,
                "disabled": True,
                "channels_sent": [NotificationChannel.SYSTEM],
                "channels_failed": [],
                "message": "用户禁用此类通知",
            }

        channels = self._determine_channels(request)
        results = self._send_to_channels(request, channels)
        self._update_dedup_cache(request)

        sent_channels = [r.channel for r in results if r.success]
        failed_channels = [r.channel for r in results if not r.success]

        return {
            "success": len(sent_channels) > 0,
            "deduped": False,
            "channels_sent": sent_channels,
            "channels_failed": failed_channels,
            "results": results,
            "message": f"发送到{len(sent_channels)}个渠道",
        }

    def send_bulk_notification(
        self, requests: List[NotificationRequest]
    ) -> List[Dict[str, Any]]:
        """批量发送通知"""
        return [self.send_notification(req) for req in requests]

    def send_task_assigned(
        self, recipient_id: int, task_id: int, task_name: str, assigner_name: str
    ) -> Dict[str, Any]:
        """发送任务分配通知"""
        request = NotificationRequest(
            recipient_id=recipient_id,
            notification_type="TASK_ASSIGNED",
            category="task",
            title="新任务分配",
            content=f"您被分配了新任务：{task_name}，分配人：{assigner_name}",
            priority=NotificationPriority.NORMAL,
            source_type="task",
            source_id=task_id,
            link_url=f"/tasks/{task_id}",
            extra_data={"task_id": task_id, "assigner_name": assigner_name},
        )
        return self.send_notification(request)

    def send_task_completed(
        self, recipient_id: int, task_id: int, task_name: str
    ) -> Dict[str, Any]:
        """发送任务完成通知"""
        request = NotificationRequest(
            recipient_id=recipient_id,
            notification_type="TASK_COMPLETED",
            category="task",
            title="任务已完成",
            content=f"任务 {task_name} 已完成",
            priority=NotificationPriority.NORMAL,
            source_type="task",
            source_id=task_id,
            link_url=f"/tasks/{task_id}",
        )
        return self.send_notification(request)

    def send_approval_pending(
        self, recipient_id: int, approval_id: int, title: str, submitter_name: str
    ) -> Dict[str, Any]:
        """发送审批待处理通知"""
        request = NotificationRequest(
            recipient_id=recipient_id,
            notification_type="APPROVAL_PENDING",
            category="approval",
            title="待处理审批",
            content=f"您有新的审批待处理：{title}，提交人：{submitter_name}",
            priority=NotificationPriority.HIGH,
            source_type="approval",
            source_id=approval_id,
            link_url=f"/approvals/{approval_id}",
            extra_data={"approval_id": approval_id, "submitter_name": submitter_name},
        )
        return self.send_notification(request)

    def send_approval_result(
        self,
        recipient_id: int,
        approval_id: int,
        title: str,
        approved: bool,
        comment: str,
    ) -> Dict[str, Any]:
        """发送审批结果通知"""
        request = NotificationRequest(
            recipient_id=recipient_id,
            notification_type="APPROVAL_RESULT",
            category="approval",
            title="审批结果",
            content=f"审批 {title} {'通过' if approved else '拒绝'}\n原因：{comment}",
            priority=NotificationPriority.NORMAL,
            source_type="approval",
            source_id=approval_id,
            link_url=f"/approvals/{approval_id}",
        )
        return self.send_notification(request)

    def send_alert(
        self, recipient_id: int, alert_id: int, alert_title: str, alert_level: str
    ) -> Dict[str, Any]:
        """发送预警通知"""
        priority = (
            NotificationPriority.URGENT
            if alert_level == "CRITICAL"
            else NotificationPriority.HIGH
            if alert_level == "WARNING"
            else NotificationPriority.NORMAL
        )
        request = NotificationRequest(
            recipient_id=recipient_id,
            notification_type="ALERT",
            category="alert",
            title=alert_title,
            content=f"预警：{alert_title}",
            priority=priority,
            source_type="alert",
            source_id=alert_id,
            link_url=f"/alerts/{alert_id}",
        )
        return self.send_notification(request)

    def send_ecn_submitted(
        self, recipient_id: int, ecn_id: int, ecn_number: str, submitter_name: str
    ) -> Dict[str, Any]:
        """发送ECN提交通知"""
        request = NotificationRequest(
            recipient_id=recipient_id,
            notification_type="ECN_SUBMITTED",
            category="ecn",
            title="ECN已提交",
            content=f"ECN {ecn_number} 已提交，提交人：{submitter_name}",
            priority=NotificationPriority.HIGH,
            source_type="ecn",
            source_id=ecn_id,
            link_url=f"/ecns?ecnId={ecn_id}",
        )
        return self.send_notification(request)

    def send_deadline_reminder(
        self,
        recipient_id: int,
        deadline_type: str,
        deadline_name: str,
        deadline_date: str,
    ) -> Dict[str, Any]:
        """发送截止日期提醒"""
        request = NotificationRequest(
            recipient_id=recipient_id,
            notification_type="DEADLINE_REMINDER",
            category="deadline",
            title="截止日期提醒",
            content=f"{deadline_name} 将于 {deadline_date} 截止",
            priority=NotificationPriority.NORMAL,
            source_type="deadline",
            link_url=None,
        )
        return self.send_notification(request)

    @staticmethod
    def send_notification_legacy(
        db: Session,
        recipient_id: int,
        notification_type: str,
        title: str,
        content: str,
        priority: str = "normal",
        channels: Optional[List[str]] = None,
        data: Optional[Dict] = None,
        link: Optional[str] = None,
    ) -> bool:
        """向后兼容的send_notification方法"""
        service = NotificationService(db)
        request = NotificationRequest(
            recipient_id=recipient_id,
            notification_type=notification_type,
            category="general",
            title=title,
            content=content,
            priority=priority,
            channels=channels,
            extra_data=data,
            link_url=link,
        )
        result = service.send_notification(request)
        return result.get("success", False)

    @staticmethod
    def create_alert_notification(
        db: Session, alert: Alert, notify_channel: str, status: str = "pending"
    ) -> AlertNotification:
        """创建预警通知记录（向后兼容）"""
        notification = AlertNotification(
            alert_id=alert.id,
            notify_user_id=alert.assignee_id,
            notify_channel=notify_channel,
            status=status,
        )
        db.add(notification)
        db.commit()
        return notification


notification_service_instance = None


def get_notification_service(db: Session) -> NotificationService:
    """获取NotificationService单例"""
    global notification_service_instance
    if (
        notification_service_instance is None
        or notification_service_instance.db is not db
    ):
        notification_service_instance = NotificationService(db)
    return notification_service_instance


notification_service = get_notification_service
