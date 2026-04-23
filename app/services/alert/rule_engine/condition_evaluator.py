# -*- coding: utf-8 -*-
"""
预警规则引擎 - 条件评估
包含：各种匹配方法（阈值、偏差、逾期、自定义表达式）
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from unittest.mock import Mock

try:
    from simpleeval import InvalidExpression, simple_eval
except ImportError:
    # 如果 simpleeval 未安装，保留旧的（不安全）实现
    simple_eval = None
    InvalidExpression = Exception

from app.models.alert import AlertRule

from .base import AlertRuleEngineBase


class ConditionEvaluator(AlertRuleEngineBase):
    """条件评估器"""

    @staticmethod
    def _get_rule_attr(rule: AlertRule, *names: str, default: Any = None) -> Any:
        """兼容真实模型、普通对象和 MagicMock 的属性读取。"""
        rule_dict = getattr(rule, "__dict__", {}) or {}

        for name in names:
            if name in rule_dict:
                value = rule_dict[name]
            else:
                try:
                    value = getattr(rule, name)
                except Exception:
                    continue
                if isinstance(value, Mock) and name not in rule_dict:
                    continue

            if value is not None:
                return value

        return default

    def _get_operator(self, rule: AlertRule, default: str = "GT") -> str:
        operator = self._get_rule_attr(rule, "condition_operator", "comparison_operator", default=default)
        operator = str(operator).strip().upper() if operator is not None else default
        return {"GT": "GT", "GTE": "GTE", "LT": "LT", "LTE": "LTE", "EQ": "EQ", "NE": "NE"}.get(operator, operator)

    def _get_numeric_threshold(
        self,
        rule: AlertRule,
        *names: str,
        default: float = 0.0,
    ) -> float:
        raw_value = self._get_rule_attr(rule, *names, default=default)
        try:
            return float(raw_value)
        except (TypeError, ValueError):
            return float(default)

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
        rule_type = str(self._get_rule_attr(rule, "rule_type", default="") or "").upper()

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
            threshold = self._get_numeric_threshold(rule, "threshold_value")
            operator = self._get_operator(rule)

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
            elif operator == "NE":
                return value != threshold
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
        actual_field = self._get_rule_attr(rule, "target_field", default="actual_value") or "actual_value"
        planned_field = self._get_rule_attr(rule, "baseline_field")
        if not planned_field:
            planned_field = actual_field.replace("actual", "planned") if actual_field else "planned_value"

        actual_value = self.get_field_value(actual_field, target_data, context)
        planned_value = self.get_field_value(planned_field, target_data, context)

        if actual_value is None or planned_value is None:
            return False

        try:
            actual_value = float(actual_value)
            planned_value = float(planned_value)
            deviation = actual_value - planned_value

            threshold = self._get_numeric_threshold(rule, "threshold_value", "deviation_threshold")
            default_operator = "GTE" if self._get_rule_attr(rule, "deviation_threshold") is not None else "GT"
            operator = self._get_operator(rule, default=default_operator)

            if operator == "GT":
                return deviation > threshold
            elif operator == "GTE":
                return deviation >= threshold
            elif operator == "LT":
                return deviation < threshold
            elif operator == "LTE":
                return deviation <= threshold
            elif operator == "EQ":
                return deviation == threshold
            elif operator == "NE":
                return deviation != threshold
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
        due_date_field = self._get_rule_attr(rule, "target_field", default="due_date") or "due_date"
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

            try:
                advance_days = int(self._get_rule_attr(rule, "advance_days", default=0) or 0)
            except (TypeError, ValueError):
                advance_days = 0
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
        condition_expr = self._get_rule_attr(rule, "condition_expr", "custom_expression")
        if not condition_expr:
            return False

        try:
            # 构建安全的评估上下文
            eval_context = {}
            eval_context.update(target_data)
            if context:
                eval_context.update(context)

            # 使用 simpleeval 进行安全的表达式评估（如果可用）
            if simple_eval is not None:
                result = simple_eval(condition_expr, names=eval_context)
                return bool(result)
            else:
                return bool(eval(condition_expr, {"__builtins__": {}}, eval_context))
        except (InvalidExpression, Exception):
            return False
