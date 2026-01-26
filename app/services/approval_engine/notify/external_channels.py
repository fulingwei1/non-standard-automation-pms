# -*- coding: utf-8 -*-
"""
审批通知服务 - 外部渠道

提供邮件、企业微信等外部渠道通知功能
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ExternalChannelsMixin:
    """外部渠道通知 Mixin"""

    def _queue_email_notification(self, notification: Dict[str, Any]):
        """
        将邮件通知加入队列

        注：实际生产环境建议使用 Celery 异步任务
        目前仅记录日志，后续集成邮件服务
        """
        logger.info(f"[邮件队列] 审批通知: {notification.get('title')}")
        # TODO: 集成邮件发送服务
        # from app.services.email_service import send_email_async
        # send_email_async.delay(receiver_id, subject, content)

    def _queue_wechat_notification(self, notification: Dict[str, Any]):
        """
        将企业微信通知加入队列

        注：实际生产环境建议使用 Celery 异步任务
        目前仅记录日志，后续集成企微 SDK
        """
        logger.info(f"[企微队列] 审批通知: {notification.get('title')}")
        # TODO: 集成企业微信 SDK
        # from app.services.wechat_service import send_wechat_async
        # send_wechat_async.delay(receiver_id, message)
