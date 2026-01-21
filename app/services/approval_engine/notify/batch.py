# -*- coding: utf-8 -*-
"""
审批通知服务 - 批量通知

提供批量发送通知功能
"""

from typing import Any, Dict, List

class BatchNotificationMixin:
    """批量通知 Mixin"""

    def batch_notify(self, notifications: List[Dict[str, Any]]):
        """
        批量发送通知

        Args:
            notifications: 通知列表
        """
        for notification in notifications:
            self._send_notification(notification)
