# -*- coding: utf-8 -*-
"""
企业微信通知处理器
"""


from app.core.config import settings
from app.models.user import User
from app.services.channel_handlers.base import (
    ChannelHandler,
    NotificationRequest,
    NotificationResult,
)
from app.utils.wechat_client import WeChatClient


class WeChatChannelHandler(ChannelHandler):
    """企业微信通知处理器"""

    def send(self, request: NotificationRequest) -> NotificationResult:
        if not self.is_enabled():
            return NotificationResult(
                channel=self.channel, success=False, error_message="企业微信功能未启用"
            )

        recipient = self.db.query(User).filter(User.id == request.recipient_id).first()
        if not recipient or not recipient.wechat_userid:
            return NotificationResult(
                channel=self.channel,
                success=False,
                error_message="用户未绑定企业微信ID",
            )

        try:
            client = WeChatClient()

            if request.wechat_template:
                template = request.wechat_template.get("template_card", {})
                success = client.send_template_card([recipient.wechat_userid], template)
            else:
                message = {
                    "msgtype": "text",
                    "text": {"content": f"【{request.title}】\n{request.content}"},
                }
                success = client.send_message([recipient.wechat_userid], message)

            if success:
                return NotificationResult(
                    channel=self.channel, success=True, sent_at=client.last_sent_time
                )
            return NotificationResult(
                channel=self.channel, success=False, error_message="企业微信发送失败"
            )
        except Exception as e:
            self.logger.error(f"企业微信发送消息失败: {e}")
            return NotificationResult(
                channel=self.channel, success=False, error_message=str(e)
            )

    def is_enabled(self) -> bool:
        return bool(settings.WECHAT_ENABLED)
