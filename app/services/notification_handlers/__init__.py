# -*- coding: utf-8 -*-
"""
通知处理器模块

按通知渠道拆分的处理器：
- system_handler: 系统通知（站内消息）
- email_handler: 邮件通知
- wechat_handler: 企业微信通知
- sms_handler: 短信通知
"""

from app.services.notification_handlers.system_handler import SystemNotificationHandler
from app.services.notification_handlers.email_handler import EmailNotificationHandler
from app.services.notification_handlers.wechat_handler import WeChatNotificationHandler
from app.services.notification_handlers.sms_handler import SMSNotificationHandler

__all__ = [
    "SystemNotificationHandler",
    "EmailNotificationHandler",
    "WeChatNotificationHandler",
    "SMSNotificationHandler",
]
