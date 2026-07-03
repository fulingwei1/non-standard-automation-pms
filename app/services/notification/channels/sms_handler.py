# -*- coding: utf-8 -*-
"""
短信通知处理器
"""

import json
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.models.user import User
from app.services.channel_handlers.base import (
    ChannelHandler,
    NotificationRequest,
    NotificationResult,
)


class SMSChannelHandler(ChannelHandler):
    """短信通知处理器"""

    def send(self, request: NotificationRequest) -> NotificationResult:
        if not self.is_enabled():
            return NotificationResult(
                channel=self.channel, success=False, error_message="短信功能未启用"
            )

        recipient = self.db.query(User).filter(User.id == request.recipient_id).first()
        if not recipient or not recipient.phone:
            return NotificationResult(
                channel=self.channel, success=False, error_message="用户未配置手机号"
            )

        try:
            self._send_via_configured_gateway(recipient.phone, request)
        except Exception as exc:
            self.logger.warning("[短信通知] 发送给 %s 失败: %s", recipient.phone, exc)
            return NotificationResult(
                channel=self.channel,
                success=False,
                error_message=f"短信发送失败: {exc}",
            )

        self.logger.info("[短信通知] 已通过网关发送给 %s: %s", recipient.phone, request.title)
        return NotificationResult(
            channel=self.channel, success=True, sent_at=datetime.now().isoformat()
        )

    def is_enabled(self) -> bool:
        return bool(settings.SMS_ENABLED)

    def _send_via_configured_gateway(
        self,
        phone: str,
        request: NotificationRequest,
    ) -> None:
        provider = self._setting_str("SMS_PROVIDER") or "aliyun"
        if provider.lower() != "aliyun":
            raise ValueError(f"不支持的短信服务商: {provider}")

        missing = [
            name
            for name in (
                "SMS_ALIYUN_ACCESS_KEY_ID",
                "SMS_ALIYUN_ACCESS_KEY_SECRET",
                "SMS_ALIYUN_SIGN_NAME",
                "SMS_ALIYUN_TEMPLATE_CODE",
            )
            if not self._setting_str(name)
        ]
        if missing:
            raise ValueError("短信网关配置不完整")

        self._send_aliyun(phone, self._build_sms_content(request))

    def _build_sms_content(self, request: NotificationRequest) -> str:
        title = request.title or "通知"
        content = request.content or ""
        message = f"{title}: {content}".strip()
        return message[:120]

    def _send_aliyun(self, phone: str, content: str) -> None:
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcore.request import CommonRequest
        except ImportError as exc:
            raise ValueError("阿里云短信SDK未安装") from exc

        client = AcsClient(
            self._setting_str("SMS_ALIYUN_ACCESS_KEY_ID"),
            self._setting_str("SMS_ALIYUN_ACCESS_KEY_SECRET"),
            self._setting_str("SMS_ALIYUN_REGION") or "cn-hangzhou",
        )

        sms_request = CommonRequest()
        sms_request.set_accept_format("json")
        sms_request.set_domain("dysmsapi.aliyuncs.com")
        sms_request.set_method("POST")
        sms_request.set_protocol_type("https")
        sms_request.set_version("2017-05-25")
        sms_request.set_action_name("SendSms")
        sms_request.add_query_param("RegionId", self._setting_str("SMS_ALIYUN_REGION") or "cn-hangzhou")
        sms_request.add_query_param("PhoneNumbers", phone)
        sms_request.add_query_param("SignName", self._setting_str("SMS_ALIYUN_SIGN_NAME"))
        sms_request.add_query_param("TemplateCode", self._setting_str("SMS_ALIYUN_TEMPLATE_CODE"))
        sms_request.add_query_param(
            "TemplateParam",
            json.dumps({"content": content}, ensure_ascii=False),
        )

        response = client.do_action_with_exception(sms_request)
        if isinstance(response, bytes):
            response = response.decode("utf-8")
        result = json.loads(response)
        if result.get("Code") != "OK":
            raise ValueError(f"阿里云短信发送失败: {result.get('Message', 'Unknown error')}")

    @staticmethod
    def _setting_str(name: str) -> Optional[str]:
        value = getattr(settings, name, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None
