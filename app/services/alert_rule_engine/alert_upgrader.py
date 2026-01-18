# -*- coding: utf-8 -*-
"""
预警规则引擎 - 预警升级
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule

from .alert_generator import AlertGenerator
from .base import AlertRuleEngineBase


class AlertUpgrader(AlertRuleEngineBase):
    """预警升级器"""

    def __init__(self, db: Session):
        super().__init__()
        self.db = db
        # 延迟导入以避免循环导入
        self._notification_service = None
        self._subscription_service = None

    @property
    def notification_service(self):
        """延迟加载通知服务"""
        if self._notification_service is None:
            from app.services.notification_service import AlertNotificationService
            self._notification_service = AlertNotificationService(self.db)
        return self._notification_service

    @property
    def subscription_service(self):
        """延迟加载订阅服务"""
        if self._subscription_service is None:
            from app.services.alert_subscription_service import AlertSubscriptionService
            self._subscription_service = AlertSubscriptionService(self.db)
        return self._subscription_service

    def upgrade_alert(
        self,
        alert: AlertRecord,
        new_level: str,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AlertRecord:
        """
        升级预警级别

        Args:
            alert: 现有预警记录
            new_level: 新的预警级别
            target_data: 目标对象数据
            context: 上下文数据

        Returns:
            AlertRecord: 升级后的预警记录
        """
        old_level = alert.alert_level

        # 更新预警级别
        alert.alert_level = new_level
        alert.is_escalated = True
        alert.escalated_at = datetime.now()

        # 更新预警内容
        rule = alert.rule
        if rule:
            alert.alert_title = AlertGenerator.generate_alert_title(rule, target_data, new_level, context, self)
            alert.alert_content = AlertGenerator.generate_alert_content(rule, target_data, new_level, context, self)

            # 更新触发值
            if rule.target_field:
                trigger_value = self.get_field_value(rule.target_field, target_data, context)
                if trigger_value is not None:
                    alert.trigger_value = str(trigger_value)

        self.db.add(alert)
        self.db.flush()

        # 发送升级通知（使用订阅匹配）
        try:
            # 获取通知接收人（基于订阅配置）
            recipients = self.subscription_service.get_notification_recipients(alert, rule)

            if recipients['user_ids']:
                # 有匹配的订阅，发送通知（升级通知强制发送）
                self.notification_service.send_alert_notification(
                    alert=alert,
                    user_ids=recipients['user_ids'],
                    channels=recipients['channels'],
                    force_send=True  # 升级通知强制发送，忽略免打扰时段
                )
            else:
                # 没有匹配的订阅，使用规则默认配置
                self.notification_service.send_alert_notification(
                    alert=alert,
                    force_send=True
                )
        except Exception as e:
            # 通知发送失败不影响升级操作
            import logging
            logging.getLogger(__name__).error(f"升级通知发送失败: {e}")

        return alert

    def check_level_escalation(
        self,
        alert: AlertRecord,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[AlertRecord]:
        """
        检查预警级别是否需要动态提升

        Args:
            alert: 现有预警记录
            target_data: 目标对象数据
            context: 上下文数据

        Returns:
            AlertRecord: 如果级别提升，返回更新后的预警；否则返回 None
        """
        if not alert.rule:
            return None

        # 检查是否在24小时内已升级过
        if alert.is_escalated and alert.escalated_at:
            time_since_escalation = datetime.now() - alert.escalated_at
            if time_since_escalation < timedelta(hours=24):
                return None

        # 重新评估条件，确定新的预警级别
        from .level_determiner import LevelDeterminer
        new_level = LevelDeterminer.determine_alert_level(alert.rule, target_data, context, self)

        # 如果新级别更高，则升级
        if self.level_priority(new_level) > self.level_priority(alert.alert_level):
            return self.upgrade_alert(alert, new_level, target_data, context)

        return None
