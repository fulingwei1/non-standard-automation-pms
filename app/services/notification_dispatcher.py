# -*- coding: utf-8 -*-
"""
Notification dispatcher for alert channels (system/WeChat/email).
Provides simple retry and logging helpers.
"""

import logging
import json
from datetime import datetime, timedelta, date
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.models.alert import AlertNotification, AlertRecord
from app.models.notification import Notification, NotificationSettings
from app.models.user import User
from app.utils.scheduler_metrics import (
    record_notification_failure,
    record_notification_success,
)
from app.core.config import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import time


class NotificationDispatcher:
    """Dispatch alert notifications to specific channels."""

    RETRY_SCHEDULE = [5, 15, 30, 60]  # minutes

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def _compute_next_retry(self, retry_count: int) -> datetime:
        idx = min(retry_count, len(self.RETRY_SCHEDULE)) - 1
        minutes = self.RETRY_SCHEDULE[idx] if idx >= 0 else self.RETRY_SCHEDULE[0]
        return datetime.now() + timedelta(minutes=minutes)

    def dispatch(self, notification: AlertNotification, alert: AlertRecord, user: Optional[User]) -> bool:
        """Send notification based on channel."""
        channel = (notification.notify_channel or "SYSTEM").upper()
        try:
            if channel == "SYSTEM":
                self._send_system(notification, alert, user)
            elif channel == "EMAIL":
                self._send_email(notification, alert, user)
            elif channel == "WECHAT":
                self._send_wechat(notification, alert, user)
            elif channel == "SMS":
                self._send_sms(notification, alert, user)
            else:
                raise ValueError(f"Unsupported notify channel: {channel}")

            notification.status = "SENT"
            notification.sent_at = datetime.now()
            notification.error_message = None
            notification.next_retry_at = None
            notification.retry_count = notification.retry_count or 0
            record_notification_success(channel)
            return True
        except Exception as exc:
            notification.status = "FAILED"
            notification.error_message = str(exc)
            notification.retry_count = (notification.retry_count or 0) + 1
            notification.next_retry_at = self._compute_next_retry(notification.retry_count)
            record_notification_failure(channel)
            self.logger.error(
                f"[notification] channel={channel} alert_id={alert.id} target={notification.notify_target} "
                f"failed: {exc}"
            )
            return False

    # Channel implementations -------------------------------------------------

    def _send_system(self, notification: AlertNotification, alert: AlertRecord, user: Optional[User]) -> None:
        """Create an in-app notification record."""
        user_id = notification.notify_user_id
        if not user_id:
            raise ValueError("System notification requires notify_user_id")

        existing = (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.source_type == "alert",
                Notification.source_id == alert.id,
                Notification.notification_type == "ALERT_NOTIFICATION",
            )
            .first()
        )
        if existing:
            return

        self.db.add(
            Notification(
                user_id=user_id,
                notification_type="ALERT_NOTIFICATION",
                title=notification.notify_title or alert.alert_title,
                content=notification.notify_content or alert.alert_content,
                source_type="alert",
                source_id=alert.id,
                link_url=f"/alerts/{alert.id}",
                priority=alert.alert_level,
                extra_data={
                    "alert_no": alert.alert_no,
                    "alert_level": alert.alert_level,
                    "target_type": alert.target_type,
                    "target_name": alert.target_name,
                },
            )
        )

    def _send_email(self, notification: AlertNotification, alert: AlertRecord, user: Optional[User]) -> None:
        """Send email notification with HTML template (if EMAIL_ENABLED)."""
        if not settings.EMAIL_ENABLED:
            raise ValueError("Email channel disabled")
        recipient = notification.notify_target or (user.email if user else None)
        if not recipient:
            raise ValueError("Email channel requires recipient email")
        if not all([settings.EMAIL_SMTP_SERVER, settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD]):
            raise ValueError("Email SMTP settings not configured")
        
        # 根据预警级别选择颜色
        from app.models.enums import AlertLevelEnum
        level_colors = {
            AlertLevelEnum.URGENT.value: "#dc2626",      # 红色
            AlertLevelEnum.CRITICAL.value: "#ea580c",    # 橙色
            AlertLevelEnum.WARNING.value: "#f59e0b",     # 黄色
            AlertLevelEnum.INFO.value: "#3b82f6",       # 蓝色
        }
        level_color = level_colors.get(alert.alert_level, "#6b7280")
        
        # 构建邮件内容
        title = notification.notify_title or alert.alert_title
        content = notification.notify_content or alert.alert_content
        
        # 构建前端URL
        frontend_url = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:3000"
        alert_url = f"{frontend_url}/alerts/{alert.id}"
        
        # 加载HTML模板
        import os
        from pathlib import Path
        
        template_path = Path(__file__).parent.parent / "templates" / "email" / "alert_notification.html"
        if not template_path.exists():
            # 如果模板不存在，使用简单的HTML格式
            html_content = f"""
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
                    {f'<p><strong>项目名称:</strong> {alert.project.project_name}</p>' if alert.project else ''}
                    <p><strong>触发时间:</strong> {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S') if alert.triggered_at else ''}</p>
                    <p><strong>状态:</strong> {alert.status}</p>
                    <hr>
                    <p>{content}</p>
                </div>
                <p><a href="{alert_url}" class="button">查看预警详情</a></p>
            </body>
            </html>
            """
        else:
            # 读取模板文件
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # 替换模板变量
            html_content = template_content.replace("{{ level_color }}", level_color)
            html_content = html_content.replace("{{ alert_level }}", alert.alert_level)
            html_content = html_content.replace("{{ alert_title }}", title)
            html_content = html_content.replace("{{ alert_no }}", alert.alert_no)
            html_content = html_content.replace("{{ project_name }}", alert.project.project_name if alert.project else "")
            html_content = html_content.replace("{{ project_code }}", alert.project.project_code if alert.project else "")
            html_content = html_content.replace("{{ triggered_at }}", alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S') if alert.triggered_at else "")
            html_content = html_content.replace("{{ status }}", alert.status)
            html_content = html_content.replace("{{ alert_content }}", content.replace('\n', '<br>'))
            html_content = html_content.replace("{{ alert_url }}", alert_url)
            # 处理条件语句（简单的模板处理）
            if not alert.project:
                html_content = html_content.replace("{% if project_name %}", "<!--")
                html_content = html_content.replace("{% endif %}", "-->")
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg["From"] = settings.EMAIL_FROM or settings.EMAIL_USERNAME
        msg["To"] = recipient
        msg["Subject"] = f"[{alert.alert_level}] {title}"
        
        # 添加纯文本版本（作为备选）
        text_content = f"""
预警通知

预警级别: {alert.alert_level}
预警标题: {title}
预警编号: {alert.alert_no}
项目名称: {alert.project.project_name if alert.project else '未知'}
触发时间: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S') if alert.triggered_at else ''}
状态: {alert.status}

预警内容:
{content}

查看详情: {alert_url}
"""
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        
        # 添加HTML版本
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        
        # 发送邮件
        with smtplib.SMTP(settings.EMAIL_SMTP_SERVER, settings.EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            server.send_message(msg)

    def _send_wechat(self, notification: AlertNotification, alert: AlertRecord, user: Optional[User]) -> None:
        """Send enterprise WeChat notification via API."""
        if not settings.WECHAT_ENABLED:
            raise ValueError("WeChat channel disabled")
        
        # 检查企业微信配置
        if not all([settings.WECHAT_CORP_ID, settings.WECHAT_AGENT_ID, settings.WECHAT_SECRET]):
            # 如果API配置不完整，尝试使用webhook（向后兼容）
            webhook = settings.WECHAT_WEBHOOK_URL
            if webhook:
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
                return
            else:
                raise ValueError("WeChat API or webhook not configured")
        
        # 使用企业微信API发送
        from app.utils.wechat_client import WeChatClient
        from app.models.enums import AlertLevelEnum
        
        # 获取用户的企业微信userid
        wechat_userid = None
        if user:
            # 尝试从Employee/Organization获取wechat_userid
            try:
                from app.models.organization import Employee
                employee = self.db.query(Employee).filter(Employee.id == user.employee_id).first()
                if employee and employee.wechat_userid:
                    wechat_userid = employee.wechat_userid
            except Exception:
                pass
            
            # 如果没有，使用username作为fallback（企业微信userid可以是username）
            if not wechat_userid and user.username:
                wechat_userid = user.username
        
        if not wechat_userid:
            raise ValueError("User WeChat userid not found. Please configure wechat_userid in employee profile or use username as fallback.")
        
        # 构建消息内容
        title = notification.notify_title or alert.alert_title
        content = notification.notify_content or alert.alert_content
        
        # 根据预警级别选择消息模板
        alert_level = alert.alert_level
        if alert_level in [AlertLevelEnum.URGENT.value, AlertLevelEnum.CRITICAL.value]:
            # 紧急/严重级别：使用卡片消息
            project_name = alert.project.project_name if alert.project else "未知项目"
            alert_url = f"{settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else 'http://localhost:3000'}/alerts/{alert.id}"
            
            template_card = {
                "card_type": "text_notice",
                "source": {
                    # 使用预警级别对应的图标颜色
                    "icon_url": _get_alert_icon_url(alert_level),
                    "desc": "预警通知",
                    "desc_color": 1  # 灰色
                },
                "main_title": {
                    "title": title,
                    "desc": f"项目：{project_name}"
                },
                "emphasis_content": {
                    "title": alert_level,
                    "desc": "请及时处理"
                },
                "quote_area": {
                    "type": 1,
                    "title": "预警详情",
                    "quote_text": content[:200]  # 限制长度
                },
                "sub_title_text": f"预警编号：{alert.alert_no}",
                "horizontal_content_list": [
                    {
                        "keyname": "触发时间",
                        "value": alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S") if alert.triggered_at else ""
                    },
                    {
                        "keyname": "状态",
                        "value": alert.status
                    }
                ],
                "jump_list": [
                    {
                        "type": 1,
                        "title": "查看详情",
                        "url": alert_url
                    }
                ],
                "card_action": {
                    "type": 1,
                    "url": alert_url
                }
            }
            
            client = WeChatClient()
            success = client.send_template_card([wechat_userid], template_card)
            if not success:
                raise ValueError("Failed to send WeChat template card message")
        else:
            # 警告/信息级别：使用文本消息
            message_content = f"【{title}】\n\n{content}\n\n预警编号：{alert.alert_no}"
            if alert.project:
                message_content += f"\n项目：{alert.project.project_name}"
            if alert.triggered_at:
                message_content += f"\n触发时间：{alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}"
            
            client = WeChatClient()
            success = client.send_text_message([wechat_userid], message_content)
            if not success:
                raise ValueError("Failed to send WeChat text message")
    
    def _send_sms(self, notification: AlertNotification, alert: AlertRecord, user: Optional[User]) -> None:
        """Send SMS notification (only for URGENT level alerts)."""
        from app.models.enums import AlertLevelEnum
        
        # 仅对URGENT级别预警发送短信
        if alert.alert_level != AlertLevelEnum.URGENT.value:
            raise ValueError("SMS notifications are only sent for URGENT level alerts")
        
        if not settings.SMS_ENABLED:
            raise ValueError("SMS channel disabled")
        
        recipient = notification.notify_target or (user.phone if user else None)
        if not recipient:
            raise ValueError("SMS channel requires recipient phone number")
        
        # 检查成本控制（简单的内存计数，生产环境建议使用Redis）
        if not hasattr(self, '_sms_count'):
            self._sms_count = {"today": {}, "hour": {}}
        
        from datetime import datetime, date
        today = date.today().isoformat()
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        
        # 检查每日限制
        daily_count = self._sms_count["today"].get(today, 0)
        if daily_count >= settings.SMS_MAX_PER_DAY:
            raise ValueError(f"SMS daily limit reached ({settings.SMS_MAX_PER_DAY})")
        
        # 检查每小时限制
        hourly_count = self._sms_count["hour"].get(current_hour, 0)
        if hourly_count >= settings.SMS_MAX_PER_HOUR:
            raise ValueError(f"SMS hourly limit reached ({settings.SMS_MAX_PER_HOUR})")
        
        # 构建短信内容
        title = notification.notify_title or alert.alert_title
        frontend_url = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:3000"
        alert_url = f"{frontend_url}/alerts/{alert.id}"
        
        # 短信内容简洁（限制70字以内）
        sms_content = f"【预警通知】{title[:30]}{'...' if len(title) > 30 else ''} 详情：{alert_url}"
        if len(sms_content) > 70:
            sms_content = f"【预警】{title[:20]} {alert_url}"
        
        # 根据提供商发送短信
        if settings.SMS_PROVIDER == "aliyun":
            self._send_sms_aliyun(recipient, sms_content)
        elif settings.SMS_PROVIDER == "tencent":
            self._send_sms_tencent(recipient, sms_content)
        else:
            raise ValueError(f"Unsupported SMS provider: {settings.SMS_PROVIDER}")
        
        # 更新计数
        self._sms_count["today"][today] = daily_count + 1
        self._sms_count["hour"][current_hour] = hourly_count + 1
    
    def _send_sms_aliyun(self, phone: str, content: str) -> None:
        """Send SMS via Aliyun SMS service."""
        try:
            # 尝试导入阿里云SDK
            try:
                from aliyunsdkcore.client import AcsClient
                from aliyunsdkcore.request import CommonRequest
            except ImportError:
                raise ValueError("Aliyun SMS SDK not installed. Install with: pip install aliyun-python-sdk-core aliyun-python-sdk-dysmsapi")
            
            if not all([settings.SMS_ALIYUN_ACCESS_KEY_ID, settings.SMS_ALIYUN_ACCESS_KEY_SECRET, 
                       settings.SMS_ALIYUN_SIGN_NAME, settings.SMS_ALIYUN_TEMPLATE_CODE]):
                raise ValueError("Aliyun SMS settings not configured")
            
            client = AcsClient(
                settings.SMS_ALIYUN_ACCESS_KEY_ID,
                settings.SMS_ALIYUN_ACCESS_KEY_SECRET,
                settings.SMS_ALIYUN_REGION
            )
            
            request = CommonRequest()
            request.set_accept_format('json')
            request.set_domain('dysmsapi.aliyuncs.com')
            request.set_method('POST')
            request.set_protocol_type('https')
            request.set_version('2017-05-25')
            request.set_action_name('SendSms')
            
            request.add_query_param('RegionId', settings.SMS_ALIYUN_REGION)
            request.add_query_param('PhoneNumbers', phone)
            request.add_query_param('SignName', settings.SMS_ALIYUN_SIGN_NAME)
            request.add_query_param('TemplateCode', settings.SMS_ALIYUN_TEMPLATE_CODE)
            request.add_query_param('TemplateParam', f'{{"content":"{content}"}}')
            
            response = client.do_action_with_exception(request)
            result = json.loads(response)
            
            if result.get('Code') != 'OK':
                raise ValueError(f"Aliyun SMS failed: {result.get('Message', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Failed to send SMS via Aliyun: {str(e)}")
            raise
    
    def _send_sms_tencent(self, phone: str, content: str) -> None:
        """Send SMS via Tencent Cloud SMS service."""
        try:
            # 尝试导入腾讯云SDK
            try:
                from tencentcloud.common import credential
                from tencentcloud.common.profile.client_profile import ClientProfile
                from tencentcloud.common.profile.http_profile import HttpProfile
                from tencentcloud.sms.v20210111 import sms_client, models
            except ImportError:
                raise ValueError("Tencent Cloud SMS SDK not installed. Install with: pip install tencentcloud-sdk-python")
            
            # 注意：这里需要配置腾讯云的SecretId和SecretKey
            # 由于配置项中没有，这里只是示例实现
            raise ValueError("Tencent Cloud SMS configuration not implemented. Please configure SMS_TENCENT_SECRET_ID and SMS_TENCENT_SECRET_KEY in config.py")
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS via Tencent: {str(e)}")
            raise


def resolve_channels(alert: AlertRecord) -> list:
    """Resolve configured channels for an alert rule."""
    if alert.rule and alert.rule.notify_channels:
        channels = [channel.upper() for channel in alert.rule.notify_channels]
        return channels or ["SYSTEM"]
    return ["SYSTEM"]


def resolve_recipients(db: Session, alert: AlertRecord) -> Dict[int, Dict[str, Optional[User]]]:
    """Return user_id -> {'user': User, 'settings': NotificationSettings or None} map."""
    user_ids = set()
    if alert.project and alert.project.pm_id:
        user_ids.add(alert.project.pm_id)
    if alert.handler_id:
        user_ids.add(alert.handler_id)
    if alert.rule and alert.rule.notify_users:
        for uid in alert.rule.notify_users:
            if isinstance(uid, int):
                user_ids.add(uid)

    if not user_ids:
        # fallback to admin user (ID=1)
        user_ids.add(1)

    users = (
        db.query(User)
        .filter(User.id.in_(user_ids))
        .filter(User.is_active == True)  # noqa: E712
        .all()
    )
    settings_map = {}
    if users:
        user_id_list = [user.id for user in users]
        settings_list = (
            db.query(NotificationSettings)
            .filter(NotificationSettings.user_id.in_(user_id_list))
            .all()
        )
        settings_map = {setting.user_id: setting for setting in settings_list}
    return {
        user.id: {"user": user, "settings": settings_map.get(user.id)}
        for user in users
    }


def resolve_channel_target(channel: str, user: Optional[User]) -> Optional[str]:
    """Determine target identifier for a given channel."""
    if not user:
        return None
    channel = channel.upper()
    if channel == "SYSTEM":
        return str(user.id)
    if channel == "EMAIL":
        return user.email
    if channel in ("WECHAT", "WE_COM"):
        return user.username or user.phone
    if channel == "SMS":
        return user.phone
    return None


def channel_allowed(channel: str, settings: Optional[NotificationSettings]) -> bool:
    """Check if user's notification settings allow a given channel."""
    if not settings:
        return True
    channel = channel.upper()
    if channel == "SYSTEM":
        return settings.system_enabled
    if channel == "EMAIL":
        return settings.email_enabled
    if channel in ("WECHAT", "WE_COM"):
        return settings.wechat_enabled
    if channel == "SMS":
        return settings.sms_enabled
    return True


def parse_time_str(value: Optional[str]) -> Optional[time]:
    if not value:
        return None
    try:
        hour, minute = value.split(":")
        return time(int(hour), int(minute))
    except Exception:
        return None


def is_quiet_hours(settings: Optional[NotificationSettings], current_time: datetime) -> bool:
    if not settings:
        return False
    start = parse_time_str(settings.quiet_hours_start)
    end = parse_time_str(settings.quiet_hours_end)
    if not start or not end:
        return False
    now = current_time.time()
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end


def next_quiet_resume(settings: NotificationSettings, current_time: datetime) -> datetime:
    end = parse_time_str(settings.quiet_hours_end)
    if not end:
        return current_time + timedelta(minutes=30)
    resume = datetime.combine(current_time.date(), end)
    if resume <= current_time:
        resume += timedelta(days=1)
    return resume


def _get_alert_icon_url(alert_level: str) -> str:
    """
    根据预警级别返回对应的图标URL
    使用通用图标服务或可以配置为自定义图标
    """
    # 使用预警级别对应的颜色图标（来自免费图标库）
    # 可以通过环境变量 ALERT_ICON_BASE_URL 自定义基础URL
    base_url = getattr(settings, 'ALERT_ICON_BASE_URL', '')

    # 预警级别与图标映射
    icon_map = {
        'URGENT': 'https://img.icons8.com/color/96/alarm--v1.png',
        'CRITICAL': 'https://img.icons8.com/color/96/high-priority--v1.png',
        'WARNING': 'https://img.icons8.com/color/96/warning--v1.png',
        'INFO': 'https://img.icons8.com/color/96/info--v1.png',
        'TIPS': 'https://img.icons8.com/color/96/light-bulb--v1.png'
    }

    return icon_map.get(alert_level.upper(), icon_map['INFO'])
