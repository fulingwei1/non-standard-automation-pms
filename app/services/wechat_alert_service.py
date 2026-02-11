# -*- coding: utf-8 -*-
"""
企业微信预警消息推送服务
实现缺料预警的企业微信卡片消息推送

此模块专注于缺料预警场景的企业微信推送。
通用的企业微信通知请使用:
- notification_handlers/wechat_handler.py (WeChatNotificationHandler)
- channel_handlers/wechat_handler.py (WeChatChannelHandler)
底层 API 客户端: utils/wechat_client.py (WeChatClient)
"""

import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session

from app.models import (
    Machine,
    MaterialReadiness,
    Project,
    ShortageAlertRule,
    ShortageDetail,
    User,
)


class WeChatAlertService:
    """企业微信预警消息推送服务
    实现缺料预警的企业微信卡片消息推送

    BACKWARD COMPATIBILITY: This service now uses unified NotificationService.
    """

    def __init__(self, db: Session):
        self.db = db
        self.unified_service = None

    def _get_unified_service(self):
        """获取统一的NotificationService单例"""
        if self.unified_service is None:
            from app.services.unified_notification_service import notification_service

            self.unified_service = notification_service(self.db)
        return self.unified_service

    @classmethod
    def send_shortage_alert(
        cls, db: Session, shortage_detail: ShortageDetail, alert_level: str
    ) -> bool:
        """
        发送缺料预警消息到企业微信

        Args:
            db: 数据库会话
            shortage_detail: 缺料明细
            alert_level: 预警级别 (L1/L2/L3/L4)
        """
        # 获取关联信息
        readiness = (
            db.query(MaterialReadiness)
            .filter(MaterialReadiness.id == shortage_detail.readiness_id)
            .first()
        )

        if not readiness:
            return False

        project = db.query(Project).filter(Project.id == readiness.project_id).first()
        if not project:
            return False

        machine = None
        if readiness.machine_id:
            machine = (
                db.query(Machine).filter(Machine.id == readiness.machine_id).first()
            )

        # 获取预警规则
        rule = (
            db.query(ShortageAlertRule)
            .filter(
                ShortageAlertRule.alert_level == alert_level,
                ShortageAlertRule.is_active == True,
            )
            .first()
        )

        # 构建消息
        message = cls._build_alert_message(
            db, shortage_detail, readiness, project, machine, alert_level, rule
        )

        # 获取通知人员
        notify_users = cls._get_notify_users(db, rule, project)

        # 发送消息
        success_count = 0
        for user in notify_users:
            if cls._send_wechat_message(db, user, message):
                success_count += 1

        return success_count > 0

    @classmethod
    def _build_alert_message(
        cls,
        db: Session,
        shortage: ShortageDetail,
        readiness: MaterialReadiness,
        project: Project,
        machine: Optional[Machine],
        alert_level: str,
        rule: Optional[ShortageAlertRule],
    ) -> Dict:
        """
        构建企业微信卡片消息

        根据设计文档7.4.1的企业微信消息模板
        """
        # 预警级别配置
        level_config = {
            "L1": {
                "title": "🔴 【停工预警】缺料导致无法装配",
                "color": "#FF0000",
                "icon": "⚠️",
            },
            "L2": {
                "title": "🟠 【紧急预警】缺料影响装配进度",
                "color": "#FF6600",
                "icon": "⚠️",
            },
            "L3": {
                "title": "🟡 【提前预警】缺料需提前准备",
                "color": "#FFCC00",
                "icon": "📢",
            },
            "L4": {"title": "🔵 【常规预警】缺料提醒", "color": "#0066CC", "icon": "ℹ️"},
        }

        config = level_config.get(alert_level, level_config["L4"])

        # 计算预计延误天数
        delay_days = 0
        if shortage.expected_arrival and project.planned_start_date:
            delay_days = (shortage.expected_arrival - project.planned_start_date).days

        # 获取当前可做到的阶段
        stage_rates = readiness.stage_kit_rates or {}
        current_stage = readiness.current_workable_stage or "未开始"

        # 构建卡片消息
        message = {
            "msgtype": "template_card",
            "template_card": {
                "card_type": "text_notice",
                "source": {
                    "icon_url": "https://example.com/icon.png",  # 应用图标
                    "desc": "缺料预警系统",
                    "desc_color": 0,
                },
                "main_title": {
                    "title": config["title"],
                    "desc": f"项目：{project.project_no} - {project.name}",
                },
                "emphasis_content": {
                    "title": "阻塞物料",
                    "desc": f"{shortage.material_name}\n缺{float(shortage.shortage_qty)}个",
                },
                "sub_title_text": f"影响：{shortage.assembly_stage}阶段无法开始\n当前可做到：{current_stage}",
                "horizontal_content_list": [
                    {"keyname": "物料编码", "value": shortage.material_code},
                    {
                        "keyname": "缺料数量",
                        "value": f"{float(shortage.shortage_qty)} {shortage.unit or '件'}",
                    },
                    {
                        "keyname": "预计到货",
                        "value": shortage.expected_arrival.strftime("%Y-%m-%d")
                        if shortage.expected_arrival
                        else "未确定",
                    },
                    {
                        "keyname": "预计延误",
                        "value": f"{delay_days}天" if delay_days > 0 else "无延误",
                    },
                ],
                "jump_list": [
                    {
                        "type": 1,
                        "url": f"https://example.com/assembly-kit?readiness_id={readiness.id}",
                        "title": "查看详情",
                    }
                ],
                "card_action": {
                    "type": 1,
                    "url": f"https://example.com/assembly-kit?readiness_id={readiness.id}",
                    "appid": "",
                    "pagepath": "",
                },
            },
        }

        # 如果是L1级别，添加更多信息
        if alert_level == "L1":
            # 获取所有阻塞物料
            from app.models import ShortageDetail as SD

            all_blocking = (
                db.query(SD)
                .filter(
                    SD.readiness_id == readiness.id,
                    SD.is_blocking == True,
                    SD.shortage_qty > 0,
                )
                .limit(5)
                .all()
            )

            if len(all_blocking) > 1:
                blocking_list = "\n".join(
                    [
                        f"• {item.material_name} 缺{float(item.shortage_qty)}个"
                        for item in all_blocking[:3]
                    ]
                )
                message["template_card"]["emphasis_content"]["desc"] = blocking_list

        return message

    @classmethod
    def _get_notify_users(
        cls, db: Session, rule: Optional[ShortageAlertRule], project: Project
    ) -> List[User]:
        """
        获取需要通知的用户列表

        根据预警规则配置的通知角色获取用户
        """
        from app.models import Role, User, UserRole

        if not rule or not rule.notify_roles:
            # 默认通知项目负责人和PMC负责人
            users = []
            if project.project_manager_id:
                pm = (
                    db.query(User).filter(User.id == project.project_manager_id).first()
                )
                if pm:
                    users.append(pm)
            return users

        # 解析通知角色（JSON格式）
        try:
            notify_roles = (
                json.loads(rule.notify_roles)
                if isinstance(rule.notify_roles, str)
                else rule.notify_roles
            )
        except (json.JSONDecodeError, TypeError):
            notify_roles = []

        if not notify_roles:
            return []

        # 根据角色获取用户
        users = []
        for role_code in notify_roles:
            role = db.query(Role).filter(Role.code == role_code).first()
            if role:
                user_roles = (
                    db.query(UserRole).filter(UserRole.role_id == role.id).all()
                )
                for ur in user_roles:
                    user = db.query(User).filter(User.id == ur.user_id).first()
                    if user and user not in users:
                        users.append(user)

        return users

    @classmethod
    def _send_wechat_message(cls, db: Session, user: User, message: Dict) -> bool:
        """
        发送企业微信消息

        通过统一通知服务发送，避免重复实现发送逻辑。
        """
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import (
            NotificationChannel,
            NotificationRequest,
            NotificationPriority,
        )

        title = ""
        content = ""
        template_card = message.get("template_card") if isinstance(message, dict) else None
        if template_card:
            main_title = template_card.get("main_title", {})
            title = main_title.get("title", "")
            content = main_title.get("desc", "")
        if not title:
            title = "缺料预警通知"
        if not content:
            content = "缺料预警通知，请查看详情。"

        request = NotificationRequest(
            recipient_id=user.id,
            notification_type="shortage_alert",
            category="alert",
            title=title,
            content=content,
            priority=NotificationPriority.URGENT,
            channels=[NotificationChannel.WECHAT],
            wechat_template=message if template_card else None,
            force_send=True,
        )

        dispatcher = NotificationDispatcher(db)
        result = dispatcher.send_notification_request(request)
        success = result.get("success", False)
        if success:
            logger.info("企业微信消息发送成功: %s", user.username)
        else:
            logger.warning("企业微信消息发送失败: %s", user.username)
        return success

    @classmethod
    def batch_send_alerts(cls, db: Session, alert_level: Optional[str] = None) -> Dict:
        """
        批量发送缺料预警

        返回发送统计
        """
        query = db.query(ShortageDetail).filter(
            ShortageDetail.shortage_qty > 0, ShortageDetail.alert_level.isnot(None)
        )

        if alert_level:
            query = query.filter(ShortageDetail.alert_level == alert_level)

        shortages = query.all()

        success_count = 0
        fail_count = 0

        for shortage in shortages:
            try:
                if cls.send_shortage_alert(db, shortage, shortage.alert_level):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"企业微信发送预警失败: {e}")
                fail_count += 1

        return {"total": len(shortages), "success": success_count, "failed": fail_count}
