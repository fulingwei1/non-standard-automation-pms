# -*- coding: utf-8 -*-
"""
Webhook通知处理器（钉钉、飞书等）
"""

from datetime import datetime
from typing import Dict, Any

import requests

from app.core.config import settings
from app.services.channel_handlers.base import (
    ChannelHandler,
    NotificationRequest,
    NotificationResult,
)


class WebhookChannelHandler(ChannelHandler):
    """Webhook通知处理器"""

    def send(self, request: NotificationRequest) -> NotificationResult:
        if not self.is_enabled():
            return NotificationResult(
                channel=self.channel, success=False, error_message="Webhook未配置"
            )

        message = self._build_message(request)
        try:
            response = requests.post(
                settings.WECHAT_WEBHOOK_URL, json=message, timeout=10
            )
            if response.status_code == 200:
                return NotificationResult(
                    channel=self.channel,
                    success=True,
                    sent_at=datetime.now().isoformat(),
                )
            return NotificationResult(
                channel=self.channel,
                success=False,
                error_message=f"Webhook返回状态码: {response.status_code}",
            )
        except Exception as e:
            self.logger.error(f"发送Webhook通知失败: {e}")
            return NotificationResult(
                channel=self.channel, success=False, error_message=str(e)
            )

    def _build_message(self, request: NotificationRequest) -> Dict[str, Any]:
        if request.wechat_template:
            return request.wechat_template
        return {
            "msgtype": "text",
            "text": {"content": f"【{request.title}】\n{request.content}"},
        }

    def is_enabled(self) -> bool:
        return bool(settings.WECHAT_WEBHOOK_URL)
