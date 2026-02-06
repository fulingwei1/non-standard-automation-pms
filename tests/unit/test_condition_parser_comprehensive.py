# -*- coding: utf-8 -*-
"""
ConditionEvaluator 综合单元测试

测试覆盖:
- __init__: 初始化评估器
- evaluate: 评估表达式
- _evaluate_jinja2: 评估Jinja2表达式
- _evaluate_simple_conditions: 评估简单条件JSON
- _evaluate_single_condition: 评估单个简单条件
- _get_field_value: 获取字段值
- _compare_values: 比较两个值
- _evaluate_sql_like: 评估SQL-like表达式
- _parse_sql_condition: 解析单个SQL条件
- _parse_value: 解析值字符串
"""

from unittest.mock import MagicMock, patch
from datetime import date, datetime
from decimal import Decimal
import json

import pytest


class TestConditionEvaluatorInit:
    """测试 ConditionEvaluator 初始化"""

    def test_initializes_successfully(self):
        """测试成功初始化"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert evaluator._jinja_env is not None

    def test_registers_filters(self):
        """测试注册过滤器"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert "length" in evaluator._jinja_env.filters
        assert "sum_by" in evaluator._jinja_env.filters
        assert "count_by" in evaluator._jinja_env.filters
        assert "percentage" in evaluator._jinja_env.filters
        assert "default" in evaluator._jinja_env.filters


class TestEvaluate:
    """测试 evaluate 方法"""

    def test_returns_none_for_empty_expression(self):
        """测试空表达式返回None"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator.evaluate("", {})

        assert result is None

    def test_detects_jinja2_syntax(self):
        """测试识别Jinja2语法"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator.evaluate("{{ value }}", {"value": 42})

        assert result == 42

    def test_detects_json_syntax(self):
        """测试识别JSON语法"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        condition = json.dumps({
            "operator": "AND",
            "items": [
                {"field": "value", "op": ">", "value": 10}
            ]
        })

        result = evaluator.evaluate(condition, {"value": 20})

        assert result is True

    def test_detects_sql_syntax(self):
        """测试识别SQL语法"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator.evaluate("value > 10", {"value": 20})

        assert result is True


class TestEvaluateJinja2:
    """测试 _evaluate_jinja2 方法"""

    def test_evaluates_simple_variable(self):
        """测试评估简单变量"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._evaluate_jinja2("{{ name }}", {"name": "张三"})

        assert result == "张三"

    def test_evaluates_numeric_variable(self):
        """测试评估数值变量"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._evaluate_jinja2("{{ count }}", {"count": 100})

        assert result == 100

    def test_evaluates_float_variable(self):
        """测试评估浮点数变量"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._evaluate_jinja2("{{ rate }}", {"rate": 3.14})

        assert result == 3.14

    def test_uses_length_filter(self):
        """测试使用length过滤器"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._evaluate_jinja2("{{ items | length }}", {"items": [1, 2, 3]})

        assert result == 3

    def test_uses_sum_by_filter(self):
        """测试使用sum_by过滤器"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        items = [{"amount": 10}, {"amount": 20}, {"amount": 30}]
        result = evaluator._evaluate_jinja2("{{ items | sum_by('amount') }}", {"items": items})

        assert result == 60

    def test_uses_count_by_filter(self):
        """测试使用count_by过滤器"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        items = [{"status": "DONE"}, {"status": "PENDING"}, {"status": "DONE"}]
        result = evaluator._evaluate_jinja2(
            "{{ items | count_by('status', 'DONE') }}", {"items": items}
        )

        assert result == 2

    def test_uses_percentage_filter(self):
        """测试使用percentage过滤器"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._evaluate_jinja2("{{ value | percentage(2) }}", {"value": 3.14159})

        assert result == 3.14

    def test_raises_for_syntax_error(self):
        """测试语法错误抛出异常"""
        from app.services.approval_engine.condition_parser import (
            ConditionEvaluator,
            ConditionParseError,
        )

        evaluator = ConditionEvaluator()

        with pytest.raises(ConditionParseError):
            evaluator._evaluate_jinja2("{{ invalid syntax {{", {})


class TestEvaluateSimpleConditions:
    """测试 _evaluate_simple_conditions 方法"""

    def test_returns_true_for_empty_conditions(self):
        """测试空条件返回True"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._evaluate_simple_conditions({}, {})

        assert result is True

    def test_evaluates_and_conditions(self):
        """测试AND条件"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        conditions = {
            "operator": "AND",
            "items": [
                {"field": "a", "op": ">", "value": 5},
                {"field": "b", "op": "<", "value": 10}
            ]
        }

        result = evaluator._evaluate_simple_conditions(conditions, {"a": 10, "b": 5})

        assert result is True

    def test_evaluates_or_conditions(self):
        """测试OR条件"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        conditions = {
            "operator": "OR",
            "items": [
                {"field": "a", "op": ">", "value": 100},
                {"field": "b", "op": "<", "value": 10}
            ]
        }

        result = evaluator._evaluate_simple_conditions(conditions, {"a": 50, "b": 5})

        assert result is True

    def test_fails_and_conditions(self):
        """测试AND条件失败"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        conditions = {
            "operator": "AND",
            "items": [
                {"field": "a", "op": ">", "value": 5},
                {"field": "b", "op": ">", "value": 100}
            ]
        }

        result = evaluator._evaluate_simple_conditions(conditions, {"a": 10, "b": 5})

        assert result is False


class TestEvaluateSingleCondition:
    """测试 _evaluate_single_condition 方法"""

    def test_evaluates_equality(self):
        """测试相等条件"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        condition = {"field": "status", "op": "==", "value": "ACTIVE"}

        result = evaluator._evaluate_single_condition(condition, {"status": "ACTIVE"})

        assert result is True

    def test_evaluates_greater_than(self):
        """测试大于条件"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        condition = {"field": "amount", "op": ">", "value": 100}

        result = evaluator._evaluate_single_condition(condition, {"amount": 150})

        assert result is True

    def test_evaluates_less_than_equal(self):
        """测试小于等于条件"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        condition = {"field": "days", "op": "<=", "value": 5}

        result = evaluator._evaluate_single_condition(condition, {"days": 3})

        assert result is True


class TestGetFieldValue:
    """测试 _get_field_value 方法"""

    def test_returns_direct_value(self):
        """测试返回直接值"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._get_field_value("name", {"name": "测试"})

        assert result == "测试"

    def test_returns_nested_value(self):
        """测试返回嵌套值"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        context = {"form": {"leave_days": 3}}

        result = evaluator._get_field_value("form.leave_days", context)

        assert result == 3

    def test_returns_none_for_missing(self):
        """测试缺失时返回None"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._get_field_value("nonexistent", {})

        assert result is None

    def test_returns_today_for_today_function(self):
        """测试today()函数返回今天日期"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._get_field_value("today()", {})

        assert result == date.today()

    def test_returns_user_attribute(self):
        """测试返回用户属性"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        context = {"user": {"name": "张三", "department": "研发部"}}

        result = evaluator._get_field_value("user.name", context)

        assert result == "张三"


class TestCompareValues:
    """测试 _compare_values 方法"""

    def test_equal_operator(self):
        """测试相等运算符"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert evaluator._compare_values(10, "==", 10) is True
        assert evaluator._compare_values(10, "==", 20) is False

    def test_not_equal_operator(self):
        """测试不等运算符"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert evaluator._compare_values(10, "!=", 20) is True
        assert evaluator._compare_values(10, "!=", 10) is False

    def test_greater_than_operator(self):
        """测试大于运算符"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert evaluator._compare_values(20, ">", 10) is True
        assert evaluator._compare_values(10, ">", 20) is False

    def test_less_than_operator(self):
        """测试小于运算符"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert evaluator._compare_values(10, "<", 20) is True
        assert evaluator._compare_values(20, "<", 10) is False

    def test_in_operator(self):
        """测试in运算符"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert evaluator._compare_values("A", "in", ["A", "B", "C"]) is True
        assert evaluator._compare_values("D", "in", ["A", "B", "C"]) is False

    def test_not_in_operator(self):
        """测试not_in运算符"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert evaluator._compare_values("D", "not_in", ["A", "B", "C"]) is True
        assert evaluator._compare_values("A", "not_in", ["A", "B", "C"]) is False

    def test_between_operator(self):
        """测试between运算符"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert evaluator._compare_values(15, "between", [10, 20]) is True
        assert evaluator._compare_values(25, "between", [10, 20]) is False

    def test_contains_operator(self):
        """测试contains运算符"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert evaluator._compare_values("hello world", "contains", "world") is True
        assert evaluator._compare_values("hello", "contains", "world") is False

    def test_starts_with_operator(self):
        """测试starts_with运算符"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert evaluator._compare_values("hello world", "starts_with", "hello") is True
        assert evaluator._compare_values("hello world", "starts_with", "world") is False

    def test_ends_with_operator(self):
        """测试ends_with运算符"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert evaluator._compare_values("hello world", "ends_with", "world") is True
        assert evaluator._compare_values("hello world", "ends_with", "hello") is False

    def test_is_null_operator(self):
        """测试is_null运算符"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert evaluator._compare_values(None, "is_null", True) is True
        assert evaluator._compare_values("value", "is_null", True) is False

    def test_regex_operator(self):
        """测试regex运算符"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        assert evaluator._compare_values("abc123", "regex", r"abc\d+") is True
        assert evaluator._compare_values("xyz", "regex", r"abc\d+") is False


class TestEvaluateSqlLike:
    """测试 _evaluate_sql_like 方法"""

    def test_evaluates_simple_condition(self):
        """测试评估简单条件"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._evaluate_sql_like("amount > 100", {"amount": 150})

        assert result is True

    def test_evaluates_and_condition(self):
        """测试评估AND条件"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._evaluate_sql_like(
            "amount > 100 AND status == 'ACTIVE'",
            {"amount": 150, "status": "ACTIVE"}
        )

        assert result is True

    def test_returns_true_for_empty(self):
        """测试空表达式返回True"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._evaluate_sql_like("", {})

        assert result is True


class TestParseSqlCondition:
    """测试 _parse_sql_condition 方法"""

    def test_parses_is_null(self):
        """测试解析IS NULL"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._parse_sql_condition("value IS NULL", {"value": None})

        assert result is True

    def test_parses_is_not_null(self):
        """测试解析IS NOT NULL"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._parse_sql_condition("value IS NOT NULL", {"value": "test"})

        assert result is True

    def test_parses_in(self):
        """测试解析IN"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._parse_sql_condition("status IN (ACTIVE, PENDING)", {"status": "ACTIVE"})

        assert result is True

    def test_parses_between(self):
        """测试解析BETWEEN"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._parse_sql_condition("amount BETWEEN 10 AND 100", {"amount": 50})

        assert result is True


class TestParseValue:
    """测试 _parse_value 方法"""

    def test_parses_integer(self):
        """测试解析整数"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._parse_value("123")

        assert result == 123

    def test_parses_float(self):
        """测试解析浮点数"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._parse_value("45.67")

        assert result == 45.67

    def test_parses_boolean_true(self):
        """测试解析布尔值true"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._parse_value("true")

        assert result is True

    def test_parses_boolean_false(self):
        """测试解析布尔值false"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._parse_value("false")

        assert result is False

    def test_parses_quoted_string(self):
        """测试解析带引号字符串"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._parse_value("'hello world'")

        assert result == "hello world"

    def test_parses_double_quoted_string(self):
        """测试解析双引号字符串"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._parse_value('"test value"')

        assert result == "test value"

    def test_parses_unquoted_string(self):
        """测试解析无引号字符串"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._parse_value("ACTIVE")

        assert result == "ACTIVE"


class TestFilters:
    """测试Jinja2过滤器"""

    def test_length_filter_with_none(self):
        """测试length过滤器处理None"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._evaluate_jinja2("{{ value | length }}", {"value": None})

        assert result == 0

    def test_sum_by_filter_with_empty_list(self):
        """测试sum_by过滤器处理空列表"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._evaluate_jinja2("{{ items | sum_by('amount') }}", {"items": []})

        assert result == 0

    def test_count_by_filter_without_value(self):
        """测试count_by过滤器不指定值"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        items = [{"a": 1}, {"a": 2}, {"a": 3}]
        result = evaluator._evaluate_jinja2("{{ items | count_by('a') }}", {"items": items})

        assert result == 3

    def test_default_filter(self):
        """测试default过滤器"""
        from app.services.approval_engine.condition_parser import ConditionEvaluator

        evaluator = ConditionEvaluator()

        result = evaluator._evaluate_jinja2("{{ value | default(10) }}", {"value": None})

        assert result == 10
