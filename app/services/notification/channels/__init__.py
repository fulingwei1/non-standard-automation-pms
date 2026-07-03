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

# 各渠道处理器采用惰性导入（PEP 562），避免 channels.base 被
# unified_adapter 导入时连带触发 *_handler，进而回环导入 handlers.* 造成循环依赖。
_LAZY_HANDLERS = {
    "EmailChannelHandler": ".email_handler",
    "SMSChannelHandler": ".sms_handler",
    "SystemChannelHandler": ".system_handler",
    "WebhookChannelHandler": ".webhook_handler",
    "WeChatChannelHandler": ".wechat_handler",
}

__all__ = [
    "ChannelHandler",
    "NotificationResult",
    "SystemChannelHandler",
    "EmailChannelHandler",
    "WeChatChannelHandler",
    "SMSChannelHandler",
    "WebhookChannelHandler",
]


def __getattr__(name):
    module_path = _LAZY_HANDLERS.get(name)
    if module_path is not None:
        import importlib

        module = importlib.import_module(module_path, __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
