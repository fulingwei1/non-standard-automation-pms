# -*- coding: utf-8 -*-
"""
预警订阅匹配服务

实现预警订阅匹配逻辑，在预警生成时根据用户订阅配置决定是否发送通知
"""

import logging
from datetime import datetime, time
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule, AlertSubscription
from app.models.enums import AlertLevelEnum


logger = logging.getLogger(__name__)


class AlertSubscriptionService:
    """预警订阅匹配服务"""

    # 预警级别优先级（用于比较）
    LEVEL_PRIORITY = {
        AlertLevelEnum.INFO.value: 1,
        AlertLevelEnum.WARNING.value: 2,
        AlertLevelEnum.CRITICAL.value: 3,
        AlertLevelEnum.URGENT.value: 4,
    }

    def __init__(self, db: Session):
        self.db = db

    def match_subscriptions(
        self,
        alert: AlertRecord,
        rule: Optional[AlertRule] = None
    ) -> List[AlertSubscription]:
        """
        匹配预警的订阅配置

        Args:
            alert: 预警记录
            rule: 预警规则（可选，如果未提供则从 alert.rule 获取）

        Returns:
            List[AlertSubscription]: 匹配的订阅配置列表
        """
        if not rule:
            rule = alert.rule
            if not rule:
                return []

        # 查询匹配的订阅配置
        query = self.db.query(AlertSubscription).filter(
            AlertSubscription.is_active
        )

        # 预警类型匹配：订阅的 alert_type 为空（全部）或与规则的 rule_type 匹配
        query = query.filter(
            or_(
                AlertSubscription.alert_type.is_(None),
                AlertSubscription.alert_type == rule.rule_type
            )
        )

        # 项目匹配：订阅的 project_id 为空（全部）或与预警的 project_id 匹配
        if alert.project_id:
            query = query.filter(
                or_(
                    AlertSubscription.project_id.is_(None),
                    AlertSubscription.project_id == alert.project_id
                )
            )
        else:
            # 如果预警没有项目ID，只匹配全部项目的订阅
            query = query.filter(AlertSubscription.project_id.is_(None))

        subscriptions = query.all()

        # 过滤：检查预警级别是否满足最低接收级别
        matched_subscriptions = []
        for subscription in subscriptions:
            if self._check_level_match(alert.alert_level, subscription.min_level):
                # 检查是否在免打扰时段
                if not self._is_quiet_hours(subscription):
                    matched_subscriptions.append(subscription)

        return matched_subscriptions

    def get_notification_recipients(
        self,
        alert: AlertRecord,
        rule: Optional[AlertRule] = None
    ) -> Dict[str, Any]:
        """
        获取预警的通知接收人列表

        Args:
            alert: 预警记录
            rule: 预警规则（可选）

        Returns:
            dict: 包含通知用户ID列表和渠道配置的字典
                {
                    'user_ids': [1, 2, 3],
                    'channels': ['SYSTEM', 'EMAIL'],
                    'subscriptions': [AlertSubscription, ...]
                }
        """
        if not rule:
            rule = alert.rule
            if not rule:
                return {
                    'user_ids': [],
                    'channels': ['SYSTEM'],
                    'subscriptions': []
                }

        # 匹配订阅配置
        subscriptions = self.match_subscriptions(alert, rule)

        # 收集用户ID和通知渠道
        user_ids: Set[int] = set()
        channels: Set[str] = set()

        # 从订阅配置中提取
        for subscription in subscriptions:
            user_ids.add(subscription.user_id)
            if subscription.notify_channels:
                channels.update([ch.upper() for ch in subscription.notify_channels])

        # 从规则配置中提取（如果规则有配置通知对象）
        if rule.notify_users:
            user_ids.update(rule.notify_users)

        # 如果规则有配置通知渠道，也加入
        if rule.notify_channels:
            channels.update([ch.upper() for ch in rule.notify_channels])

        # 如果没有匹配到任何订阅，使用规则默认配置
        if not subscriptions:
            # 使用规则配置的默认通知对象
            if rule.notify_users:
                user_ids.update(rule.notify_users)
            else:
                # 如果没有配置，返回空列表（不发送通知）
                # TODO: 完善实现 - 根据规则类型获取默认接收人（如项目负责人）
                logger.info("订阅默认接收人: 暂未配置 (rule_id=%s, rule_name=%s)", rule.id, rule.name)

            # 使用规则配置的默认通知渠道
            if rule.notify_channels:
                channels.update([ch.upper() for ch in rule.notify_channels])
            else:
                channels.add('SYSTEM')  # 默认使用站内消息

        return {
            'user_ids': list(user_ids),
            'channels': list(channels) if channels else ['SYSTEM'],
            'subscriptions': subscriptions
        }

    def _check_level_match(self, alert_level: str, min_level: str) -> bool:
        """
        检查预警级别是否满足最低接收级别

        Args:
            alert_level: 预警级别
            min_level: 最低接收级别

        Returns:
            bool: 是否匹配
        """
        alert_priority = self.LEVEL_PRIORITY.get(alert_level, 0)
        min_priority = self.LEVEL_PRIORITY.get(min_level, 0)
        return alert_priority >= min_priority

    def _is_quiet_hours(self, subscription: AlertSubscription) -> bool:
        """
        检查当前时间是否在免打扰时段

        Args:
            subscription: 订阅配置

        Returns:
            bool: 是否在免打扰时段
        """
        if not subscription.quiet_start or not subscription.quiet_end:
            return False

        try:
            # 解析时间字符串（HH:mm格式）
            start_parts = subscription.quiet_start.split(':')
            end_parts = subscription.quiet_end.split(':')

            quiet_start = time(int(start_parts[0]), int(start_parts[1]))
            quiet_end = time(int(end_parts[0]), int(end_parts[1]))
            current_time = datetime.now().time()

            # 处理跨天的情况（如 22:00 - 08:00）
            if quiet_start <= quiet_end:
                # 同一天内
                return quiet_start <= current_time <= quiet_end
            else:
                # 跨天
                return current_time >= quiet_start or current_time <= quiet_end
        except (ValueError, IndexError, AttributeError):
            # 时间格式错误，不启用免打扰
            return False

    def get_user_subscriptions(
        self,
        user_id: int,
        alert_type: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> List[AlertSubscription]:
        """
        获取用户的订阅配置（用于查询）

        Args:
            user_id: 用户ID
            alert_type: 预警类型（可选）
            project_id: 项目ID（可选）

        Returns:
            List[AlertSubscription]: 订阅配置列表
        """
        query = self.db.query(AlertSubscription).filter(
            AlertSubscription.user_id == user_id,
            AlertSubscription.is_active
        )

        if alert_type:
            query = query.filter(
                or_(
                    AlertSubscription.alert_type.is_(None),
                    AlertSubscription.alert_type == alert_type
                )
            )

        if project_id:
            query = query.filter(
                or_(
                    AlertSubscription.project_id.is_(None),
                    AlertSubscription.project_id == project_id
                )
            )

        return query.all()
