# -*- coding: utf-8 -*-
"""
渠道处理器基类和通用定义
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


class NotificationChannel(str):
    """通知渠道"""

    SYSTEM = "system"
    EMAIL = "email"
    WECHAT = "wechat"
    SMS = "sms"
    WEBHOOK = "webhook"


class NotificationPriority(str):
    """通知优先级"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class NotificationResult:
    """通知发送结果"""

    channel: str
    success: bool
    error_message: Optional[str] = None
    sent_at: Optional[str] = None


@dataclass
class NotificationRequest:
    """通知请求"""

    recipient_id: int
    notification_type: str
    category: str
    title: str
    content: str
    priority: str = NotificationPriority.NORMAL
    channels: Optional[List[str]] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    link_url: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    wechat_template: Optional[Dict[str, Any]] = None


class ChannelHandler(ABC):
    """渠道处理器基类"""

    def __init__(self, db, channel: str):
        self.db = db
        self.channel = channel
        self.logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    @abstractmethod
    def send(self, request: NotificationRequest) -> NotificationResult:
        """发送通知"""
        pass

    def is_enabled(self) -> bool:
        """检查渠道是否启用"""
        return True

    def should_send(self, user_settings, priority: str) -> bool:
        """检查是否应该发送（根据偏好和优先级）"""
        if not user_settings:
            return True

        priority_order = [
            NotificationPriority.URGENT,
            NotificationPriority.HIGH,
            NotificationPriority.NORMAL,
            NotificationPriority.LOW,
        ]
        priority_level = (
            priority_order.index(priority) if priority in priority_order else 1
        )

        if self.channel == NotificationChannel.SYSTEM:
            return getattr(user_settings, "system_enabled", True)
        elif self.channel == NotificationChannel.EMAIL:
            return getattr(user_settings, "email_enabled", True) or priority_level <= 1
        elif self.channel == NotificationChannel.WECHAT:
            return getattr(user_settings, "wechat_enabled", True) or priority_level <= 0
        elif self.channel == NotificationChannel.SMS:
            return getattr(user_settings, "sms_enabled", False) or priority_level <= 0
        return True
