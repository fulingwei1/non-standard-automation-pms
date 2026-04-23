# -*- coding: utf-8 -*-
"""向后兼容入口: app.services.notification_handlers."""

from app.services.notification_handlers.email_handler import EmailNotificationHandler
from app.services.notification_handlers.sms_handler import SMSNotificationHandler
from app.services.notification_handlers.system_handler import SystemNotificationHandler
from app.services.notification_handlers.wechat_handler import WeChatNotificationHandler

__all__ = [
    "SystemNotificationHandler",
    "EmailNotificationHandler",
    "WeChatNotificationHandler",
    "SMSNotificationHandler",
]
