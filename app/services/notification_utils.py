# -*- coding: utf-8 -*-
"""
通知工具函数

提供通知系统的辅助函数：渠道解析、接收者解析、免打扰判断等。

通知系统架构：
- app.services.unified_notification_service: 主通知服务，提供 NotificationService 和 get_notification_service()
- app.services.notification_service: 兼容层，re-export 统一服务并提供旧接口的枚举和 AlertNotificationService
- app.services.notification_dispatcher: 预警通知调度协调器，内部使用统一服务
- app.services.notification_queue: Redis 通知队列（异步分发）
- app.services.notification_utils (本模块): 通知工具函数（渠道解析、接收者解析、免打扰判断等）
- app.services.channel_handlers/: 渠道处理器（System/Email/WeChat/SMS/Webhook）
"""

from datetime import datetime, time, timedelta
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.models.alert import AlertRecord
from app.models.notification import NotificationSettings
from app.models.user import User


def get_alert_icon_url(alert_level: str) -> str:
    """根据预警级别返回对应的图标URL"""
    icon_map = {
        "URGENT": "https://img.icons8.com/color/96/alarm--v1.png",
        "CRITICAL": "https://img.icons8.com/color/96/high-priority--v1.png",
        "WARNING": "https://img.icons8.com/color/96/warning--v1.png",
        "INFO": "https://img.icons8.com/color/96/info--v1.png",
        "TIPS": "https://img.icons8.com/color/96/light-bulb--v1.png",
    }
    return icon_map.get(alert_level.upper(), icon_map["INFO"])


def resolve_channels(alert: AlertRecord) -> list:
    """Resolve configured channels for an alert rule."""
    if alert.rule and alert.rule.notify_channels:
        channels = [channel.upper() for channel in alert.rule.notify_channels]
        return channels or ["SYSTEM"]
    return ["SYSTEM"]


def resolve_recipients(
    db: Session, alert: AlertRecord
) -> Dict[int, Dict[str, Optional[User]]]:
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
        user_ids.add(1)

    users = (
        db.query(User)
        .filter(User.id.in_(user_ids))
        .filter(User.is_active == True)
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
        user.id: {"user": user, "settings": settings_map.get(user.id)} for user in users
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


def is_quiet_hours(
    settings: Optional[NotificationSettings], current_time: datetime
) -> bool:
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


def next_quiet_resume(
    settings: NotificationSettings, current_time: datetime
) -> datetime:
    end = parse_time_str(settings.quiet_hours_end)
    if not end:
        return current_time + timedelta(minutes=30)
    resume = datetime.combine(current_time.date(), end)
    if resume <= current_time:
        resume += timedelta(days=1)
    return resume
