# -*- coding: utf-8 -*-
"""
提醒通知发送服务
支持邮件、企业微信、系统通知
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notification import Notification
from app.models.timesheet_reminder import (
    NotificationChannelEnum,
    TimesheetReminderRecord,
)
from app.models.user import User

logger = logging.getLogger(__name__)


class NotificationSender:
    """通知发送器"""

    def __init__(self, db: Session):
        self.db = db

    def send_reminder_notification(
        self,
        reminder: TimesheetReminderRecord,
        channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        发送提醒通知
        
        Args:
            reminder: 提醒记录
            channels: 通知渠道列表（不指定则使用提醒记录中的配置）
            
        Returns:
            各渠道发送结果 {"EMAIL": True, "WECHAT": False, "SYSTEM": True}
        """
        if channels is None:
            channels = reminder.notification_channels or ['SYSTEM']

        # 获取用户信息
        user = self.db.query(User).filter(User.id == reminder.user_id).first()
        if not user:
            logger.error(f"用户不存在: {reminder.user_id}")
            return {}

        results = {}

        for channel in channels:
            try:
                if channel == 'SYSTEM':
                    success = self._send_system_notification(reminder, user)
                    results['SYSTEM'] = success
                elif channel == 'EMAIL':
                    success = self._send_email_notification(reminder, user)
                    results['EMAIL'] = success
                elif channel == 'WECHAT':
                    success = self._send_wechat_notification(reminder, user)
                    results['WECHAT'] = success
                else:
                    logger.warning(f"不支持的通知渠道: {channel}")
                    results[channel] = False
            except Exception as e:
                logger.error(f"发送{channel}通知失败: {str(e)}")
                results[channel] = False

        # 记录发送结果
        successful_channels = [ch for ch, success in results.items() if success]
        logger.info(
            f"提醒通知发送完成: {reminder.reminder_no}, "
            f"成功渠道: {successful_channels}"
        )

        return results

    def _send_system_notification(
        self,
        reminder: TimesheetReminderRecord,
        user: User
    ) -> bool:
        """发送系统通知"""
        try:
            notification = Notification(
                user_id=user.id,
                notification_type=reminder.reminder_type.value,
                title=reminder.title,
                content=reminder.content,
                priority=reminder.priority,
                source_type=reminder.source_type,
                source_id=reminder.source_id,
                extra_data=reminder.extra_data,
                is_read=False,
            )

            self.db.add(notification)
            self.db.commit()

            logger.info(f"系统通知发送成功: {reminder.reminder_no}")
            return True
        except Exception as e:
            logger.error(f"发送系统通知失败: {str(e)}")
            self.db.rollback()
            return False

    def _send_email_notification(
        self,
        reminder: TimesheetReminderRecord,
        user: User
    ) -> bool:
        """发送邮件通知"""
        # 检查邮件配置
        if not hasattr(settings, 'SMTP_HOST') or not settings.SMTP_HOST:
            logger.warning("邮件服务未配置")
            return False

        if not user.email:
            logger.warning(f"用户{user.username}未配置邮箱")
            return False

        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = reminder.title
            msg['From'] = getattr(settings, 'SMTP_FROM', 'noreply@example.com')
            msg['To'] = user.email

            # 邮件内容（支持HTML）
            html_content = self._generate_email_html(reminder, user)
            text_content = reminder.content

            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')

            msg.attach(part1)
            msg.attach(part2)

            # 发送邮件
            smtp_host = settings.SMTP_HOST
            smtp_port = getattr(settings, 'SMTP_PORT', 587)
            smtp_user = getattr(settings, 'SMTP_USER', '')
            smtp_password = getattr(settings, 'SMTP_PASSWORD', '')

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if getattr(settings, 'SMTP_TLS', True):
                    server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)

            logger.info(f"邮件通知发送成功: {reminder.reminder_no} -> {user.email}")
            return True
        except Exception as e:
            logger.error(f"发送邮件通知失败: {str(e)}")
            return False

    def _send_wechat_notification(
        self,
        reminder: TimesheetReminderRecord,
        user: User
    ) -> bool:
        """发送企业微信通知"""
        # 检查企业微信配置
        if not hasattr(settings, 'WECHAT_CORP_ID') or not settings.WECHAT_CORP_ID:
            logger.warning("企业微信未配置")
            return False

        if not hasattr(user, 'wechat_user_id') or not user.wechat_user_id:
            logger.warning(f"用户{user.username}未绑定企业微信")
            return False

        try:
            # 获取access_token
            access_token = self._get_wechat_access_token()
            if not access_token:
                logger.error("获取企业微信access_token失败")
                return False

            # 构建消息
            api_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            
            message_data = {
                "touser": user.wechat_user_id,
                "msgtype": "textcard",
                "agentid": getattr(settings, 'WECHAT_AGENT_ID', 0),
                "textcard": {
                    "title": reminder.title,
                    "description": reminder.content,
                    "url": self._generate_reminder_url(reminder),
                    "btntxt": "查看详情"
                }
            }

            response = requests.post(api_url, json=message_data, timeout=10)
            result = response.json()

            if result.get('errcode') == 0:
                logger.info(f"企业微信通知发送成功: {reminder.reminder_no} -> {user.wechat_user_id}")
                return True
            else:
                logger.error(f"企业微信通知发送失败: {result}")
                return False
        except Exception as e:
            logger.error(f"发送企业微信通知失败: {str(e)}")
            return False

    def _get_wechat_access_token(self) -> Optional[str]:
        """获取企业微信access_token"""
        try:
            corp_id = settings.WECHAT_CORP_ID
            corp_secret = getattr(settings, 'WECHAT_CORP_SECRET', '')

            api_url = (
                f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?"
                f"corpid={corp_id}&corpsecret={corp_secret}"
            )

            response = requests.get(api_url, timeout=10)
            result = response.json()

            if result.get('errcode') == 0:
                return result.get('access_token')
            else:
                logger.error(f"获取access_token失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取access_token异常: {str(e)}")
            return None

    def _generate_email_html(
        self,
        reminder: TimesheetReminderRecord,
        user: User
    ) -> str:
        """生成邮件HTML内容"""
        extra_info = ""
        if reminder.extra_data:
            extra_info = "<br><br><strong>详细信息：</strong><br>"
            for key, value in reminder.extra_data.items():
                extra_info += f"• {key}: {value}<br>"

        html = f"""
        <html>
          <head></head>
          <body>
            <h2 style="color: #333;">{reminder.title}</h2>
            <p>{reminder.content}</p>
            {extra_info}
            <br>
            <p style="color: #666; font-size: 12px;">
              此邮件由系统自动发送，请勿回复。<br>
              如有疑问，请联系系统管理员。
            </p>
          </body>
        </html>
        """
        return html

    def _generate_reminder_url(self, reminder: TimesheetReminderRecord) -> str:
        """生成提醒详情链接"""
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        
        # 根据提醒类型生成不同的链接
        if reminder.source_type == 'timesheet' and reminder.source_id:
            return f"{base_url}/timesheet/{reminder.source_id}"
        elif reminder.source_type == 'timesheet_batch' and reminder.source_id:
            return f"{base_url}/timesheet/batch/{reminder.source_id}"
        else:
            return f"{base_url}/notifications"

    def send_batch_reminders(
        self,
        reminders: List[TimesheetReminderRecord],
        channels: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        批量发送提醒
        
        Returns:
            发送统计 {"total": 10, "success": 8, "failed": 2}
        """
        total = len(reminders)
        success = 0
        failed = 0

        for reminder in reminders:
            try:
                results = self.send_reminder_notification(reminder, channels)
                if any(results.values()):  # 至少一个渠道成功
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"发送提醒失败: {reminder.reminder_no}, {str(e)}")
                failed += 1

        logger.info(f"批量发送完成: 总数={total}, 成功={success}, 失败={failed}")
        return {"total": total, "success": success, "failed": failed}
