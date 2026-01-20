# -*- coding: utf-8 -*-
"""短信通知处理器"""

import json
import logging
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import AlertNotification, AlertRecord
from app.models.enums import AlertLevelEnum
from app.models.user import User

if TYPE_CHECKING:
    from app.services.notification_dispatcher import NotificationDispatcher


class SMSNotificationHandler:
    """短信通知处理器"""

    RETRY_SCHEDULE = [5, 15, 30, 60]

    def __init__(self, db: Session, parent: "NotificationDispatcher" = None):
        self.db = db
        self._parent = parent
        self.logger = logging.getLogger(__name__)
        self._sms_count = {"today": {}, "hour": {}}

    def send(
        self,
        notification: AlertNotification,
        alert: AlertRecord,
        user: Optional[User] = None,
    ) -> None:
        """
        发送短信通知（仅限URGENT级别）

        Args:
            notification: 通知对象
            alert: 预警记录
            user: 目标用户

        Raises:
            ValueError: 当配置无效或缺少必要参数时
        """
        if alert.alert_level != AlertLevelEnum.URGENT.value:
            raise ValueError("SMS notifications are only sent for URGENT level alerts")

        if not settings.SMS_ENABLED:
            raise ValueError("SMS channel disabled")

        recipient = notification.notify_target or (user.phone if user else None)
        if not recipient:
            raise ValueError("SMS channel requires recipient phone number")

        today = date.today().isoformat()
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")

        daily_count = self._sms_count["today"].get(today, 0)
        if daily_count >= settings.SMS_MAX_PER_DAY:
            raise ValueError(f"SMS daily limit reached ({settings.SMS_MAX_PER_DAY})")

        hourly_count = self._sms_count["hour"].get(current_hour, 0)
        if hourly_count >= settings.SMS_MAX_PER_HOUR:
            raise ValueError(f"SMS hourly limit reached ({settings.SMS_MAX_PER_HOUR})")

        title = notification.notify_title or alert.alert_title
        frontend_url = (
            settings.CORS_ORIGINS[0]
            if settings.CORS_ORIGINS
            else "http://localhost:3000"
        )
        alert_url = f"{frontend_url}/alerts/{alert.id}"

        sms_content = f"【预警通知】{title[:30]}{'...' if len(title) > 30 else ''} 详情：{alert_url}"
        if len(sms_content) > 70:
            sms_content = f"【预警】{title[:20]} {alert_url}"

        if settings.SMS_PROVIDER == "aliyun":
            self._send_aliyun(recipient, sms_content)
        elif settings.SMS_PROVIDER == "tencent":
            self._send_tencent(recipient, sms_content)
        else:
            raise ValueError(f"Unsupported SMS provider: {settings.SMS_PROVIDER}")

        self._sms_count["today"][today] = daily_count + 1
        self._sms_count["hour"][current_hour] = hourly_count + 1

    def _send_aliyun(self, phone: str, content: str) -> None:
        """通过阿里云发送短信"""
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcore.request import CommonRequest
        except ImportError:
            raise ValueError("Aliyun SMS SDK not installed")

        if not all(
            [
                settings.SMS_ALIYUN_ACCESS_KEY_ID,
                settings.SMS_ALIYUN_ACCESS_KEY_SECRET,
                settings.SMS_ALIYUN_SIGN_NAME,
                settings.SMS_ALIYUN_TEMPLATE_CODE,
            ]
        ):
            raise ValueError("Aliyun SMS settings not configured")

        client = AcsClient(
            settings.SMS_ALIYUN_ACCESS_KEY_ID,
            settings.SMS_ALIYUN_ACCESS_KEY_SECRET,
            settings.SMS_ALIYUN_REGION,
        )

        request = CommonRequest()
        request.set_accept_format("json")
        request.set_domain("dysmsapi.aliyuncs.com")
        request.set_method("POST")
        request.set_protocol_type("https")
        request.set_version("2017-05-25")
        request.set_action_name("SendSms")

        request.add_query_param("RegionId", settings.SMS_ALIYUN_REGION)
        request.add_query_param("PhoneNumbers", phone)
        request.add_query_param("SignName", settings.SMS_ALIYUN_SIGN_NAME)
        request.add_query_param("TemplateCode", settings.SMS_ALIYUN_TEMPLATE_CODE)
        request.add_query_param("TemplateParam", f'{{"content":"{content}"}}')

        response = client.do_action_with_exception(request)
        result = json.loads(response)

        if result.get("Code") != "OK":
            raise ValueError(
                f"Aliyun SMS failed: {result.get('Message', 'Unknown error')}"
            )

    def _send_tencent(self, phone: str, content: str) -> None:
        """通过腾讯云发送短信"""
        raise ValueError("Tencent Cloud SMS configuration not implemented")
