# -*- coding: utf-8 -*-
"""
预警规则引擎 - 条件评估
包含：各种匹配方法（阈值、偏差、逾期、自定义表达式）
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

try:
    from simpleeval import simple_eval, InvalidExpression
except ImportError:
    # 如果 simpleeval 未安装，保留旧的（不安全）实现
    simple_eval = None
    InvalidExpression = Exception

from app.models.alert import AlertRule

from .base import AlertRuleEngineBase


class ConditionEvaluator(AlertRuleEngineBase):
    """条件评估器"""

    def check_condition(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        检查规则条件是否满足

        Args:
            rule: 预警规则
            target_data: 目标对象数据
            context: 上下文数据

        Returns:
            bool: 条件是否满足
        """
        rule_type = rule.rule_type

        if rule_type == "THRESHOLD":
            return self.match_threshold(rule, target_data, context)
        elif rule_type == "DEVIATION":
            return self.match_deviation(rule, target_data, context)
        elif rule_type == "OVERDUE":
            return self.match_overdue(rule, target_data, context)
        elif rule_type == "CUSTOM":
            return self.match_custom_expr(rule, target_data, context)
        else:
            return False

    def match_threshold(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        阈值匹配

        Args:
            rule: 预警规则
            target_data: 目标对象数据
            context: 上下文数据

        Returns:
            bool: 是否匹配
        """
        field_name = rule.target_field or "value"
        value = self.get_field_value(field_name, target_data, context)

        if value is None:
            return False

        try:
            value = float(value)
            threshold = float(rule.threshold_value) if rule.threshold_value else 0
            operator = rule.condition_operator or "GT"

            if operator == "GT":
                return value > threshold
            elif operator == "GTE":
                return value >= threshold
            elif operator == "LT":
                return value < threshold
            elif operator == "LTE":
                return value <= threshold
            elif operator == "EQ":
                return value == threshold
            else:
                return False
        except (ValueError, TypeError):
            return False

    def match_deviation(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        偏差匹配

        Args:
            rule: 预警规则
            target_data: 目标对象数据
            context: 上下文数据

        Returns:
            bool: 是否匹配
        """
        actual_field = rule.target_field or "actual_value"
        planned_field = (
            rule.target_field.replace("actual", "planned")
            if rule.target_field
            else "planned_value"
        )

        actual_value = self.get_field_value(actual_field, target_data, context)
        planned_value = self.get_field_value(planned_field, target_data, context)

        if actual_value is None or planned_value is None:
            return False

        try:
            actual_value = float(actual_value)
            planned_value = float(planned_value)
            deviation = actual_value - planned_value

            threshold = float(rule.threshold_value) if rule.threshold_value else 0
            operator = rule.condition_operator or "GT"

            if operator == "GT":
                return deviation > threshold
            elif operator == "GTE":
                return deviation >= threshold
            elif operator == "LT":
                return deviation < threshold
            elif operator == "LTE":
                return deviation <= threshold
            else:
                return False
        except (ValueError, TypeError):
            return False

    def match_overdue(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        逾期匹配

        Args:
            rule: 预警规则
            target_data: 目标对象数据
            context: 上下文数据

        Returns:
            bool: 是否匹配
        """
        # 需要截止日期字段
        due_date_field = rule.target_field or "due_date"
        due_date = self.get_field_value(due_date_field, target_data, context)

        if not due_date:
            return False

        if isinstance(due_date, str):
            try:
                due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return False

        if isinstance(due_date, datetime):
            if due_date.tzinfo:
                # 使用正确的时区感知方式获取当前时间，而非 replace()
                now = datetime.now(tz=due_date.tzinfo)
            else:
                now = datetime.now()

            advance_days = rule.advance_days or 0
            check_date = due_date - timedelta(days=advance_days)

            return now >= check_date
        else:
            return False

    def match_custom_expr(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        自定义表达式匹配（简单实现，实际可以使用更复杂的表达式引擎）

        Args:
            rule: 预警规则
            target_data: 目标对象数据
            context: 上下文数据

        Returns:
            bool: 是否匹配
        """
        if not rule.condition_expr:
            return False

        try:
            # 构建安全的评估上下文
            eval_context = {}
            eval_context.update(target_data)
            if context:
                eval_context.update(context)

            # 使用 simpleeval 进行安全的表达式评估（如果可用）
            if simple_eval is not None:
                result = simple_eval(
                    rule.condition_expr,
                    names=eval_context,
                    safe=True,  # 禁用所有未授权的功能
                )
                return bool(result)
            else:
                # 后备方案：simpleeval 未安装时返回 False
                # 建议安装: pip install simpleeval==1.0.2
                return False
        except (InvalidExpression, Exception):
            return False
