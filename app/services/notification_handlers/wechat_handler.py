# -*- coding: utf-8 -*-
"""企业微信通知处理器"""

import logging
from typing import Optional, TYPE_CHECKING

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import AlertNotification, AlertRecord
from app.models.enums import AlertLevelEnum
from app.models.organization import Employee
from app.models.user import User
from app.utils.wechat_client import WeChatClient

if TYPE_CHECKING:
    from app.services.notification_dispatcher import NotificationDispatcher


class WeChatNotificationHandler:
    """企业微信通知处理器"""

    def __init__(self, db: Session, parent: "NotificationDispatcher" = None):
        self.db = db
        self._parent = parent
        self.logger = logging.getLogger(__name__)

    def send(
        self,
        notification: AlertNotification,
        alert: AlertRecord,
        user: Optional[User] = None,
    ) -> None:
        """
        发送企业微信通知

        Args:
            notification: 通知对象
            alert: 预警记录
            user: 目标用户

        Raises:
            ValueError: 当配置无效或缺少必要参数时
        """
        if not settings.WECHAT_ENABLED:
            raise ValueError("WeChat channel disabled")

        if not all(
            [settings.WECHAT_CORP_ID, settings.WECHAT_AGENT_ID, settings.WECHAT_SECRET]
        ):
            webhook = settings.WECHAT_WEBHOOK_URL
            if webhook:
                self._send_via_webhook(notification, alert, webhook)
                return
            else:
                raise ValueError("WeChat API or webhook not configured")

        self._send_via_api(notification, alert, user)

    def _send_via_webhook(
        self,
        notification: AlertNotification,
        alert: AlertRecord,
        webhook: str,
    ) -> None:
        """通过Webhook发送企业微信消息"""
        content = notification.notify_content or alert.alert_content
        payload = {
            "msgtype": "text",
            "text": {
                "content": f"{notification.notify_title or alert.alert_title}\n{content}",
            },
        }
        resp = requests.post(webhook, json=payload, timeout=5)
        if resp.status_code >= 400:
            raise ValueError(f"WeChat webhook failed: {resp.text}")

    def _send_via_api(
        self,
        notification: AlertNotification,
        alert: AlertRecord,
        user: Optional[User],
    ) -> None:
        """通过企业微信API发送消息"""
        wechat_userid = self._get_wechat_userid(user)
        if not wechat_userid:
            raise ValueError("User WeChat userid not found")

        title = notification.notify_title or alert.alert_title
        content = notification.notify_content or alert.alert_content
        alert_level = alert.alert_level

        frontend_url = (
            settings.CORS_ORIGINS[0]
            if settings.CORS_ORIGINS
            else "http://localhost:3000"
        )
        alert_url = f"{frontend_url}/alerts/{alert.id}"

        if alert_level in [AlertLevelEnum.URGENT.value, AlertLevelEnum.CRITICAL.value]:
            self._send_card_message(wechat_userid, alert, title, content, alert_url)
        else:
            self._send_text_message(wechat_userid, alert, title, content, alert_url)

    def _get_wechat_userid(self, user: Optional[User]) -> Optional[str]:
        """获取用户的企微userid"""
        if not user:
            return None

        try:
            employee = (
                self.db.query(Employee).filter(Employee.id == user.employee_id).first()
            )
            if employee and employee.wechat_userid:
                return employee.wechat_userid
        except Exception as e:
            self.logger.warning(f"获取企微userid失败: {e}, user_id: {user.id}")

        if user.username:
            return user.username
        return None

    def _send_card_message(
        self,
        wechat_userid: str,
        alert: AlertRecord,
        title: str,
        content: str,
        alert_url: str,
    ) -> None:
        """发送卡片消息（紧急/严重级别）"""
        project_name = alert.project.project_name if alert.project else "未知项目"

        template_card = {
            "card_type": "text_notice",
            "source": {
                "icon_url": get_alert_icon_url(alert.alert_level),
                "desc": "预警通知",
                "desc_color": 1,
            },
            "main_title": {
                "title": title,
                "desc": f"项目：{project_name}",
            },
            "emphasis_content": {
                "title": alert.alert_level,
                "desc": "请及时处理",
            },
            "quote_area": {
                "type": 1,
                "title": "预警详情",
                "quote_text": content[:200],
            },
            "sub_title_text": f"预警编号：{alert.alert_no}",
            "horizontal_content_list": [
                {
                    "keyname": "触发时间",
                    "value": alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S")
                    if alert.triggered_at
                    else "",
                },
                {"keyname": "状态", "value": alert.status},
            ],
            "jump_list": [{"type": 1, "title": "查看详情", "url": alert_url}],
            "card_action": {"type": 1, "url": alert_url},
        }

        client = WeChatClient()
        success = client.send_template_card([wechat_userid], template_card)
        if not success:
            raise ValueError("Failed to send WeChat template card message")

    def _send_text_message(
        self,
        wechat_userid: str,
        alert: AlertRecord,
        title: str,
        content: str,
        alert_url: str,
    ) -> None:
        """发送文本消息（警告/信息级别）"""
        message_content = f"【{title}】\n\n{content}\n\n预警编号：{alert.alert_no}"
        if alert.project:
            message_content += f"\n项目：{alert.project.project_name}"
        if alert.triggered_at:
            message_content += (
                f"\n触发时间：{alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        client = WeChatClient()
        success = client.send_text_message([wechat_userid], message_content)
        if not success:
            raise ValueError("Failed to send WeChat text message")
