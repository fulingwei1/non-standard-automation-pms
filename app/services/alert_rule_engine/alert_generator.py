# -*- coding: utf-8 -*-
"""
预警规则引擎 - 预警内容生成
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule

from .base import AlertRuleEngineBase


class AlertGenerator(AlertRuleEngineBase):
    """预警内容生成器"""

    @staticmethod
    def generate_alert_no(
        db: Session,
        rule: AlertRule,
        target_data: Dict[str, Any]
    ) -> str:
        """
        生成预警编号

        Args:
            db: 数据库会话
            rule: 预警规则
            target_data: 目标对象数据

        Returns:
            str: 预警编号
        """
        today = datetime.now().strftime('%Y%m%d')
        rule_code = rule.rule_code[:3].upper()

        # 查询今天的预警数量
        count = db.query(AlertRecord).filter(
            AlertRecord.alert_no.like(f'{rule_code}{today}%')
        ).count()

        return f'{rule_code}{today}{str(count + 1).zfill(4)}'

    @staticmethod
    def generate_alert_title(
        rule: AlertRule,
        target_data: Dict[str, Any],
        alert_level: str,
        context: Optional[Dict[str, Any]] = None,
        engine: Optional[AlertRuleEngineBase] = None
    ) -> str:
        """
        生成预警标题（子类可重写）

        Args:
            rule: 预警规则
            target_data: 目标对象数据
            alert_level: 预警级别
            context: 上下文数据
            engine: 引擎实例（用于获取字段值）

        Returns:
            str: 预警标题
        """
        target_name = target_data.get('target_name') or target_data.get('target_no') or '对象'
        return f'{rule.rule_name}：{target_name}'

    @staticmethod
    def generate_alert_content(
        rule: AlertRule,
        target_data: Dict[str, Any],
        alert_level: str,
        context: Optional[Dict[str, Any]] = None,
        engine: Optional[AlertRuleEngineBase] = None
    ) -> str:
        """
        生成预警内容（子类可重写）

        Args:
            rule: 预警规则
            target_data: 目标对象数据
            alert_level: 预警级别
            context: 上下文数据
            engine: 引擎实例（用于获取字段值）

        Returns:
            str: 预警内容
        """
        content = f'{rule.rule_name}\n'
        if rule.description:
            content += f'说明：{rule.description}\n'

        if rule.target_field and engine:
            trigger_value = engine.get_field_value(rule.target_field, target_data, context)
            if trigger_value is not None:
                content += f'当前值：{trigger_value}\n'

        if rule.threshold_value:
            content += f'阈值：{rule.threshold_value}\n'

        if rule.solution_guide:
            content += f'\n处理建议：{rule.solution_guide}'

        return content
