# -*- coding: utf-8 -*-
"""
通知渠道处理器模块

按通知渠道拆分的处理器：
- base: 基类和接口定义
- system_handler: 系统通知（站内消息）
- email_handler: 邮件通知
- wechat_handler: 企业微信通知
- sms_handler: 短信通知
- webhook_handler: Webhook通知
"""

from .base import ChannelHandler, NotificationResult
from .system_handler import SystemChannelHandler
from .email_handler import EmailChannelHandler
from .wechat_handler import WeChatChannelHandler
from .sms_handler import SMSChannelHandler
from .webhook_handler import WebhookChannelHandler

__all__ = [
    "ChannelHandler",
    "NotificationResult",
    "SystemChannelHandler",
    "EmailChannelHandler",
    "WeChatChannelHandler",
    "SMSChannelHandler",
    "WebhookChannelHandler",
]
