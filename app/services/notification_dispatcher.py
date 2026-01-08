# -*- coding: utf-8 -*-
"""
Notification dispatcher for alert channels (system/WeChat/email).
Provides simple retry and logging helpers.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.models.alert import AlertNotification, AlertRecord
from app.models.notification import Notification, NotificationSettings
from app.models.user import User
from app.utils.scheduler_metrics import (
    record_notification_failure,
    record_notification_success,
)
from app.core.config import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import time


class NotificationDispatcher:
    """Dispatch alert notifications to specific channels."""

    RETRY_SCHEDULE = [5, 15, 30, 60]  # minutes

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def _compute_next_retry(self, retry_count: int) -> datetime:
        idx = min(retry_count, len(self.RETRY_SCHEDULE)) - 1
        minutes = self.RETRY_SCHEDULE[idx] if idx >= 0 else self.RETRY_SCHEDULE[0]
        return datetime.now() + timedelta(minutes=minutes)

    def dispatch(self, notification: AlertNotification, alert: AlertRecord, user: Optional[User]) -> bool:
        """Send notification based on channel."""
        channel = (notification.notify_channel or "SYSTEM").upper()
        try:
            if channel == "SYSTEM":
                self._send_system(notification, alert, user)
            elif channel == "EMAIL":
                self._send_email(notification, alert, user)
            elif channel == "WECHAT":
                self._send_wechat(notification, alert, user)
            else:
                raise ValueError(f"Unsupported notify channel: {channel}")

            notification.status = "SENT"
            notification.sent_at = datetime.now()
            notification.error_message = None
            notification.next_retry_at = None
            notification.retry_count = notification.retry_count or 0
            record_notification_success(channel)
            return True
        except Exception as exc:
            notification.status = "FAILED"
            notification.error_message = str(exc)
            notification.retry_count = (notification.retry_count or 0) + 1
            notification.next_retry_at = self._compute_next_retry(notification.retry_count)
            record_notification_failure(channel)
            self.logger.error(
                f"[notification] channel={channel} alert_id={alert.id} target={notification.notify_target} "
                f"failed: {exc}"
            )
            return False

    # Channel implementations -------------------------------------------------

    def _send_system(self, notification: AlertNotification, alert: AlertRecord, user: Optional[User]) -> None:
        """Create an in-app notification record."""
        user_id = notification.notify_user_id
        if not user_id:
            raise ValueError("System notification requires notify_user_id")

        existing = (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.source_type == "alert",
                Notification.source_id == alert.id,
                Notification.notification_type == "ALERT_NOTIFICATION",
            )
            .first()
        )
        if existing:
            return

        self.db.add(
            Notification(
                user_id=user_id,
                notification_type="ALERT_NOTIFICATION",
                title=notification.notify_title or alert.alert_title,
                content=notification.notify_content or alert.alert_content,
                source_type="alert",
                source_id=alert.id,
                link_url=f"/alerts/{alert.id}",
                priority=alert.alert_level,
                extra_data={
                    "alert_no": alert.alert_no,
                    "alert_level": alert.alert_level,
                    "target_type": alert.target_type,
                    "target_name": alert.target_name,
                },
            )
        )

    def _send_email(self, notification: AlertNotification, alert: AlertRecord, user: Optional[User]) -> None:
        """Send email notification (if EMAIL_ENABLED)."""
        if not settings.EMAIL_ENABLED:
            raise ValueError("Email channel disabled")
        recipient = notification.notify_target or (user.email if user else None)
        if not recipient:
            raise ValueError("Email channel requires recipient email")
        if not all([settings.EMAIL_SMTP_SERVER, settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD]):
            raise ValueError("Email SMTP settings not configured")
        
        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_FROM or settings.EMAIL_USERNAME
        msg["To"] = recipient
        msg["Subject"] = notification.notify_title or alert.alert_title
        msg.attach(MIMEText(notification.notify_content or alert.alert_content, "plain", "utf-8"))
        
        with smtplib.SMTP(settings.EMAIL_SMTP_SERVER, settings.EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            server.send_message(msg)

    def _send_wechat(self, notification: AlertNotification, alert: AlertRecord, user: Optional[User]) -> None:
        """Send enterprise WeChat notification via webhook."""
        if not settings.WECHAT_ENABLED:
            raise ValueError("WeChat channel disabled")
        webhook = settings.WECHAT_WEBHOOK_URL
        if not webhook:
            raise ValueError("WeChat webhook not configured")
        content = notification.notify_content or alert.alert_content
        payload = {
            "msgtype": "text",
            "text": {
                "content": f"{notification.notify_title or alert.alert_title}\n{content}",
            },
        }
        resp = requests.post(webhook, json=payload, timeout=5)
        if resp.status_code >= 400:
            raise ValueError(f"WeChat webhook failed: {resp.text}")


def resolve_channels(alert: AlertRecord) -> list:
    """Resolve configured channels for an alert rule."""
    if alert.rule and alert.rule.notify_channels:
        channels = [channel.upper() for channel in alert.rule.notify_channels]
        return channels or ["SYSTEM"]
    return ["SYSTEM"]


def resolve_recipients(db: Session, alert: AlertRecord) -> Dict[int, Dict[str, Optional[User]]]:
    """Return user_id -> {'user': User, 'settings': NotificationSettings or None} map."""
    user_ids = set()
    if alert.project and alert.project.pm_id:
        user_ids.add(alert.project.pm_id)
    if alert.handler_id:
        user_ids.add(alert.handler_id)
    if alert.rule and alert.rule.notify_users:
        for uid in alert.rule.notify_users:
            if isinstance(uid, int):
                user_ids.add(uid)

    if not user_ids:
        # fallback to admin user (ID=1)
        user_ids.add(1)

    users = (
        db.query(User)
        .filter(User.id.in_(user_ids))
        .filter(User.is_active == True)  # noqa: E712
        .all()
    )
    settings_map = {}
    if users:
        user_id_list = [user.id for user in users]
        settings_list = (
            db.query(NotificationSettings)
            .filter(NotificationSettings.user_id.in_(user_id_list))
            .all()
        )
        settings_map = {setting.user_id: setting for setting in settings_list}
    return {
        user.id: {"user": user, "settings": settings_map.get(user.id)}
        for user in users
    }


def resolve_channel_target(channel: str, user: Optional[User]) -> Optional[str]:
    """Determine target identifier for a given channel."""
    if not user:
        return None
    channel = channel.upper()
    if channel == "SYSTEM":
        return str(user.id)
    if channel == "EMAIL":
        return user.email
    if channel in ("WECHAT", "WE_COM"):
        return user.username or user.phone
    if channel == "SMS":
        return user.phone
    return None


def channel_allowed(channel: str, settings: Optional[NotificationSettings]) -> bool:
    """Check if user's notification settings allow a given channel."""
    if not settings:
        return True
    channel = channel.upper()
    if channel == "SYSTEM":
        return settings.system_enabled
    if channel == "EMAIL":
        return settings.email_enabled
    if channel in ("WECHAT", "WE_COM"):
        return settings.wechat_enabled
    if channel == "SMS":
        return settings.sms_enabled
    return True


def parse_time_str(value: Optional[str]) -> Optional[time]:
    if not value:
        return None
    try:
        hour, minute = value.split(":")
        return time(int(hour), int(minute))
    except Exception:
        return None


def is_quiet_hours(settings: Optional[NotificationSettings], current_time: datetime) -> bool:
    if not settings:
        return False
    start = parse_time_str(settings.quiet_hours_start)
    end = parse_time_str(settings.quiet_hours_end)
    if not start or not end:
        return False
    now = current_time.time()
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end


def next_quiet_resume(settings: NotificationSettings, current_time: datetime) -> datetime:
    end = parse_time_str(settings.quiet_hours_end)
    if not end:
        return current_time + timedelta(minutes=30)
    resume = datetime.combine(current_time.date(), end)
    if resume <= current_time:
        resume += timedelta(days=1)
    return resume
