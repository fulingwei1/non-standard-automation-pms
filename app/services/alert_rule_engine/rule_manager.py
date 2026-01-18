# -*- coding: utf-8 -*-
"""
预警规则引擎 - 规则管理
"""

from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.alert import AlertRule


class RuleManager:
    """规则管理器"""

    @staticmethod
    def get_or_create_rule(
        db: Session,
        rule_code: str,
        default_config: Dict[str, Any]
    ) -> AlertRule:
        """
        获取或创建预警规则

        Args:
            db: 数据库会话
            rule_code: 规则编码
            default_config: 默认配置

        Returns:
            AlertRule: 预警规则
        """
        rule = db.query(AlertRule).filter(
            AlertRule.rule_code == rule_code
        ).first()

        if not rule:
            rule = AlertRule(
                rule_code=rule_code,
                is_system=True,
                is_enabled=True,
                **default_config
            )
            db.add(rule)
            db.flush()

        return rule
