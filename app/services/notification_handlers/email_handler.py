# -*- coding: utf-8 -*-
"""
邮件通知处理器（完整 SMTP 实现）

此模块包含完整的邮件发送实现，包括 SMTP 连接、HTML 模板和纯文本支持。
统一渠道系统中的轻量级适配器在 channel_handlers/email_handler.py 中。
"""

import logging
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import AlertNotification, AlertRecord
from app.models.user import User
from app.services.notification_handlers.unified_adapter import (
    NotificationChannel,
    send_alert_via_unified,
)

if TYPE_CHECKING:
    from app.services.notification_dispatcher import NotificationDispatcher


class EmailNotificationHandler:
    """邮件通知处理器"""

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
        发送邮件通知

        Args:
            notification: 通知对象
            alert: 预警记录
            user: 目标用户

        Raises:
            ValueError: 当配置无效或缺少必要参数时
        """
        if not settings.EMAIL_ENABLED:
            raise ValueError("Email channel disabled")
        recipient = (
            getattr(notification, "notify_target", None)
            or getattr(notification, "notify_email", None)
            or (user.email if user else None)
        )
        if not recipient and not getattr(notification, "notify_user_id", None):
            raise ValueError("Email channel requires recipient email")

        send_alert_via_unified(
            db=self.db,
            notification=notification,
            alert=alert,
            user=user,
            channel=NotificationChannel.EMAIL,
            target_field="email",
            target_value=recipient,
        )

    def _build_simple_html(
        self,
        alert: AlertRecord,
        title: str,
        content: str,
        level_color: str,
        alert_url: str,
    ) -> str:
        """构建简单HTML邮件内容"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: {level_color}; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ padding: 20px; background-color: #f9f9f9; margin: 20px 0; border-radius: 5px; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: {level_color}; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{title}</h2>
                <p>预警级别: {alert.alert_level}</p>
            </div>
            <div class="content">
                <p><strong>预警编号:</strong> {alert.alert_no}</p>
                {f"<p><strong>项目名称:</strong> {alert.project.project_name}</p>" if alert.project else ""}
                <p><strong>触发时间:</strong> {alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S") if alert.triggered_at else ""}</p>
                <p><strong>状态:</strong> {alert.status}</p>
                <hr>
                <p>{content}</p>
            </div>
            <p><a href="{alert_url}" class="button">查看预警详情</a></p>
        </body>
        </html>
        """

    def _build_html_from_template(
        self,
        alert: AlertRecord,
        title: str,
        content: str,
        level_color: str,
        alert_url: str,
        template_path: Path,
    ) -> str:
        """从模板文件构建HTML邮件内容"""
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        html_content = template_content.replace("{{ level_color }}", level_color)
        html_content = html_content.replace("{{ alert_level }}", alert.alert_level)
        html_content = html_content.replace("{{ alert_title }}", title)
        html_content = html_content.replace("{{ alert_no }}", alert.alert_no)
        html_content = html_content.replace(
            "{{ project_name }}", alert.project.project_name if alert.project else ""
        )
        html_content = html_content.replace(
            "{{ project_code }}", alert.project.project_code if alert.project else ""
        )
        html_content = html_content.replace(
            "{{ triggered_at }}",
            alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S")
            if alert.triggered_at
            else "",
        )
        html_content = html_content.replace("{{ status }}", alert.status)
        html_content = html_content.replace(
            "{{ alert_content }}", content.replace("\n", "<br>")
        )
        html_content = html_content.replace("{{ alert_url }}", alert_url)

        if not alert.project:
            html_content = html_content.replace("{% if project_name %}", "<!--")
            html_content = html_content.replace("{% endif %}", "-->")

        return html_content

    def _build_plain_text(
        self,
        alert: AlertRecord,
        title: str,
        content: str,
        alert_url: str,
    ) -> str:
        """构建纯文本邮件内容"""
        return f"""
预警通知

预警级别: {alert.alert_level}
预警标题: {title}
预警编号: {alert.alert_no}
项目名称: {alert.project.project_name if alert.project else "未知"}
触发时间: {alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S") if alert.triggered_at else ""}
状态: {alert.status}

预警内容:
{content}

查看详情: {alert_url}
"""
