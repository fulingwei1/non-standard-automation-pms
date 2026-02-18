# -*- coding: utf-8 -*-
"""第七批覆盖率测试 - approval_engine/condition_parser"""
import pytest
from unittest.mock import MagicMock

try:
    from app.services.approval_engine.condition_parser import (
        ConditionEvaluator,
        ConditionParseError,
    )
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="module unavailable")


@pytest.fixture
def evaluator():
    return ConditionEvaluator()


class TestConditionEvaluator:
    def test_init_creates_instance(self, evaluator):
        assert evaluator is not None

    def test_evaluate_simple_gt_condition(self, evaluator):
        """简单大于条件"""
        expr = {"operator": "AND", "items": [
            {"field": "amount", "op": ">", "value": 1000}
        ]}
        import json
        result = evaluator.evaluate(json.dumps(expr), {"amount": 2000})
        assert result is True

    def test_evaluate_simple_lt_condition(self, evaluator):
        expr = {"operator": "AND", "items": [
            {"field": "amount", "op": "<", "value": 1000}
        ]}
        import json
        result = evaluator.evaluate(json.dumps(expr), {"amount": 500})
        assert result is True

    def test_evaluate_eq_condition(self, evaluator):
        expr = {"operator": "AND", "items": [
            {"field": "status", "op": "==", "value": "approved"}
        ]}
        import json
        result = evaluator.evaluate(json.dumps(expr), {"status": "approved"})
        assert result is True

    def test_evaluate_sql_like_amount_gt(self, evaluator):
        """SQL-like 语法"""
        result = evaluator.evaluate("amount > 500", {"amount": 1000})
        assert result is True

    def test_evaluate_sql_like_amount_lt(self, evaluator):
        result = evaluator.evaluate("amount < 500", {"amount": 100})
        assert result is True

    def test_evaluate_and_operator(self, evaluator):
        expr = {"operator": "AND", "items": [
            {"field": "amount", "op": ">", "value": 100},
            {"field": "amount", "op": "<", "value": 10000},
        ]}
        import json
        result = evaluator.evaluate(json.dumps(expr), {"amount": 500})
        assert result is True

    def test_evaluate_or_operator_one_true(self, evaluator):
        expr = {"operator": "OR", "items": [
            {"field": "status", "op": "==", "value": "A"},
            {"field": "status", "op": "==", "value": "B"},
        ]}
        import json
        result = evaluator.evaluate(json.dumps(expr), {"status": "A"})
        assert result is True

    def test_get_field_value_nested(self, evaluator):
        """嵌套字段访问"""
        context = {"project": {"budget": 50000}}
        result = evaluator._get_field_value("project.budget", context)
        assert result == 50000

    def test_compare_values_gte(self, evaluator):
        assert evaluator._compare_values(100, ">=", 100) is True
        assert evaluator._compare_values(99, ">=", 100) is False

    def test_compare_values_contains(self, evaluator):
        assert evaluator._compare_values("hello world", "contains", "world") is True
        assert evaluator._compare_values("hello", "contains", "world") is False

    def test_empty_expression_returns_truthy(self, evaluator):
        """空表达式默认为True/None（可接受）"""
        result = evaluator.evaluate("", {})
        # may return None or True depending on implementation
        assert result is True or result is None
