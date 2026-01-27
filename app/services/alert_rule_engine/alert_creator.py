# -*- coding: utf-8 -*-
"""
预警规则引擎 - 预警创建
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule
from app.models.enums import AlertStatusEnum

from .base import AlertRuleEngineBase
from .condition_evaluator import ConditionEvaluator


class AlertCreator(ConditionEvaluator):
    """预警创建器"""

    def __init__(self, db: Session):
        super().__init__(db)
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

    def should_create_alert(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        alert_level: str
    ) -> Optional[AlertRecord]:
        """
        检查是否应该创建预警（去重逻辑）

        Args:
            rule: 预警规则
            target_data: 目标对象数据
            alert_level: 预警级别

        Returns:
            AlertRecord: 如果存在相同来源的活跃预警，返回该预警；否则返回 None
        """
        target_type = target_data.get('target_type')
        target_id = target_data.get('target_id')

        if not target_type or not target_id:
            return None

        # 查询相同来源的活跃预警（24小时内）
        time_window = datetime.now() - timedelta(hours=24)

        existing_alert = self.db.query(AlertRecord).filter(
            AlertRecord.rule_id == rule.id,
            AlertRecord.target_type == target_type,
            AlertRecord.target_id == target_id,
            AlertRecord.status.in_(['PENDING', 'ACKNOWLEDGED']),
            AlertRecord.created_at >= time_window
        ).order_by(AlertRecord.created_at.desc()).first()

        return existing_alert

    def create_alert(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        alert_level: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AlertRecord:
        """
        创建预警记录

        Args:
            rule: 预警规则
            target_data: 目标对象数据
            alert_level: 预警级别
            context: 上下文数据

        Returns:
            AlertRecord: 创建的预警记录
        """
        from .alert_generator import AlertGenerator

        # 生成预警编号
        alert_no = AlertGenerator.generate_alert_no(self.db, rule, target_data)

        # 获取触发值
        trigger_value = None
        if rule.target_field:
            trigger_value = self.get_field_value(rule.target_field, target_data, context)

        # 创建预警记录
        alert = AlertRecord(
            alert_no=alert_no,
            rule_id=rule.id,
            target_type=target_data.get('target_type'),
            target_id=target_data.get('target_id'),
            target_no=target_data.get('target_no'),
            target_name=target_data.get('target_name'),
            project_id=target_data.get('project_id'),
            machine_id=target_data.get('machine_id'),
            alert_level=alert_level,
            alert_title=AlertGenerator.generate_alert_title(rule, target_data, alert_level, context, self),
            alert_content=AlertGenerator.generate_alert_content(rule, target_data, alert_level, context, self),
            alert_data=target_data,
            status=AlertStatusEnum.PENDING.value,
            triggered_at=datetime.now(),
            trigger_value=str(trigger_value) if trigger_value is not None else None,
            threshold_value=rule.threshold_value
        )

        self.db.add(alert)
        self.db.flush()

        # 发送通知（使用订阅匹配）
        try:
            # 获取通知接收人（基于订阅配置）
            recipients = self.subscription_service.get_notification_recipients(alert, rule)

            if recipients['user_ids']:
                # 有匹配的订阅，发送通知
                self.notification_service.send_alert_notification(
                    alert=alert,
                    user_ids=recipients['user_ids'],
                    channels=recipients['channels']
                )
            else:
                # 没有匹配的订阅，使用规则默认配置
                self.notification_service.send_alert_notification(alert=alert)
        except Exception as e:
            # 通知发送失败不影响预警创建
            import logging
            logging.getLogger(__name__).error(f"预警通知发送失败: {e}")

        return alert
