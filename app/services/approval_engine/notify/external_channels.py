# -*- coding: utf-8 -*-
"""
审批通知服务 - 外部渠道（已迁移到统一服务）

外部渠道通知现在由统一通知服务处理，此类保留用于向后兼容。
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ExternalChannelsMixin:
    """外部渠道通知 Mixin（已迁移到统一服务）
    
    注意：外部渠道通知现在由统一通知服务自动处理。
    统一服务会根据用户偏好和通知优先级自动路由到合适的渠道。
    这些方法保留用于向后兼容，但不再需要手动调用。
    """

    def _queue_email_notification(self, notification: Dict[str, Any]):
        """
        将邮件通知加入队列（已由统一服务处理）
        
        注意：此方法保留用于向后兼容，但实际邮件发送已由统一服务处理。
        统一服务会根据用户偏好和通知优先级自动决定是否发送邮件。
        """
        # 统一服务已经处理了邮件通知，这里只记录日志
        logger.debug(f"[邮件] 审批通知已由统一服务处理: {notification.get('title')}")

    def _queue_wechat_notification(self, notification: Dict[str, Any]):
        """
        将企业微信通知加入队列（已由统一服务处理）
        
        注意：此方法保留用于向后兼容，但实际企微发送已由统一服务处理。
        统一服务会根据用户偏好和通知优先级自动决定是否发送企微消息。
        """
        # 统一服务已经处理了企微通知，这里只记录日志
        logger.debug(f"[企微] 审批通知已由统一服务处理: {notification.get('title')}")
