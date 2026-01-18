# -*- coding: utf-8 -*-
"""
预警规则引擎 - 预警级别确定
"""

from typing import Any, Dict, Optional

from app.models.alert import AlertRule
from app.models.enums import AlertLevelEnum

from .base import AlertRuleEngineBase


class LevelDeterminer(AlertRuleEngineBase):
    """预警级别确定器"""

    @staticmethod
    def determine_alert_level(
        rule: AlertRule,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        engine: Optional[AlertRuleEngineBase] = None
    ) -> str:
        """
        确定预警级别（子类可重写以实现更复杂的级别判断）

        Args:
            rule: 预警规则
            target_data: 目标对象数据
            context: 上下文数据
            engine: 引擎实例（用于获取字段值）

        Returns:
            str: 预警级别
        """
        # 默认使用规则配置的级别
        return rule.alert_level or AlertLevelEnum.WARNING.value
