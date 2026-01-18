# -*- coding: utf-8 -*-
"""
预警规则引擎
功能：提供统一的预警规则评估框架，支持规则条件评估、预警记录创建、预警去重和升级

向后兼容：保持原有的类接口
"""

from sqlalchemy.orm import Session

from .alert_creator import AlertCreator
from .alert_generator import AlertGenerator
from .alert_upgrader import AlertUpgrader
from .base import AlertRuleEngineBase
from .condition_evaluator import ConditionEvaluator
from .level_determiner import LevelDeterminer
from .rule_manager import RuleManager


class AlertRuleEngine(AlertCreator, AlertUpgrader):
    """预警规则引擎 - 统一接口类"""

    def __init__(self, db: Session):
        # AlertCreator 已经继承了 ConditionEvaluator 和 AlertRuleEngineBase
        AlertCreator.__init__(self, db)
        AlertUpgrader.__init__(self, db)

    def evaluate_rule(
        self,
        rule,
        target_data,
        context=None
    ):
        """
        评估规则并创建预警记录（如果条件满足）

        Args:
            rule: 预警规则
            target_data: 目标对象数据
            context: 上下文数据（可选）

        Returns:
            AlertRecord: 创建的预警记录，如果未创建则返回 None
        """
        if not rule.is_enabled:
            return None

        # 检查触发条件
        if not self.check_condition(rule, target_data, context):
            return None

        # 确定预警级别
        alert_level = LevelDeterminer.determine_alert_level(rule, target_data, context, self)

        # 检查是否应该创建预警（去重逻辑）
        existing_alert = self.should_create_alert(rule, target_data, alert_level)

        if existing_alert:
            # 如果已有预警且级别更高，升级现有预警
            if self.level_priority(alert_level) > self.level_priority(existing_alert.alert_level):
                return self.upgrade_alert(existing_alert, alert_level, target_data, context)
            # 如果级别相同或更低，不重复创建
            return None

        # 创建新的预警记录
        return self.create_alert(rule, target_data, alert_level, context)

    # 委托给 LevelDeterminer
    determine_alert_level = LevelDeterminer.determine_alert_level

    # 委托给 RuleManager
    get_or_create_rule = RuleManager.get_or_create_rule


# 向后兼容：导出主引擎类
__all__ = [
    'AlertRuleEngine',
    # 基类
    'AlertRuleEngineBase',
    # 组件类
    'ConditionEvaluator',
    'AlertCreator',
    'AlertUpgrader',
    'AlertGenerator',
    'LevelDeterminer',
    'RuleManager',
]
