# -*- coding: utf-8 -*-
"""条件评估器单元测试 - 第三十四批"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone

pytest.importorskip("app.services.alert_rule_engine.condition_evaluator")

try:
    from app.services.alert_rule_engine.condition_evaluator import ConditionEvaluator
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    ConditionEvaluator = None


def make_rule(**kwargs):
    rule = MagicMock()
    rule.rule_type = kwargs.get("rule_type", "THRESHOLD")
    rule.target_field = kwargs.get("target_field", "value")
    rule.threshold_value = kwargs.get("threshold_value", "100")
    rule.condition_operator = kwargs.get("condition_operator", "GT")
    rule.advance_days = kwargs.get("advance_days", 0)
    rule.condition_expr = kwargs.get("condition_expr", None)
    return rule


def make_evaluator():
    evaluator = ConditionEvaluator.__new__(ConditionEvaluator)
    evaluator.get_field_value = lambda field, data, ctx=None: data.get(field)
    return evaluator


class TestCheckCondition:
    def test_threshold_type_dispatches(self):
        ev = make_evaluator()
        rule = make_rule(rule_type="THRESHOLD", threshold_value="50", condition_operator="GT")
        assert ev.check_condition(rule, {"value": 60}) is True

    def test_deviation_type_dispatches(self):
        ev = make_evaluator()
        rule = make_rule(rule_type="DEVIATION", target_field="actual_value",
                         threshold_value="10", condition_operator="GT")
        data = {"actual_value": 120, "planned_value": 100}
        assert ev.check_condition(rule, data) is True

    def test_unknown_type_returns_false(self):
        ev = make_evaluator()
        rule = make_rule(rule_type="UNKNOWN")
        assert ev.check_condition(rule, {"value": 100}) is False


class TestMatchThreshold:
    def test_gt_true(self):
        ev = make_evaluator()
        rule = make_rule(threshold_value="50", condition_operator="GT")
        assert ev.match_threshold(rule, {"value": 60}) is True

    def test_gt_false(self):
        ev = make_evaluator()
        rule = make_rule(threshold_value="50", condition_operator="GT")
        assert ev.match_threshold(rule, {"value": 40}) is False

    def test_lte_true(self):
        ev = make_evaluator()
        rule = make_rule(threshold_value="100", condition_operator="LTE")
        assert ev.match_threshold(rule, {"value": 100}) is True

    def test_none_value_returns_false(self):
        ev = make_evaluator()
        rule = make_rule(threshold_value="50", condition_operator="GT")
        assert ev.match_threshold(rule, {}) is False

    def test_invalid_value_returns_false(self):
        ev = make_evaluator()
        rule = make_rule(threshold_value="50", condition_operator="GT")
        assert ev.match_threshold(rule, {"value": "not_a_number"}) is False


class TestMatchDeviation:
    def test_positive_deviation_gt(self):
        ev = make_evaluator()
        rule = make_rule(rule_type="DEVIATION", target_field="actual_value",
                         threshold_value="5", condition_operator="GT")
        data = {"actual_value": 110, "planned_value": 100}
        assert ev.match_deviation(rule, data) is True

    def test_missing_planned_returns_false(self):
        ev = make_evaluator()
        rule = make_rule(rule_type="DEVIATION", target_field="actual_value",
                         threshold_value="5", condition_operator="GT")
        data = {"actual_value": 110}
        assert ev.match_deviation(rule, data) is False


class TestMatchOverdue:
    def test_past_due_date_returns_true(self):
        ev = make_evaluator()
        rule = make_rule(rule_type="OVERDUE", target_field="due_date", advance_days=0)
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        assert ev.match_overdue(rule, {"due_date": past_date}) is True

    def test_future_due_date_returns_false(self):
        ev = make_evaluator()
        rule = make_rule(rule_type="OVERDUE", target_field="due_date", advance_days=0)
        future_date = (datetime.now() + timedelta(days=10)).isoformat()
        assert ev.match_overdue(rule, {"due_date": future_date}) is False

    def test_missing_due_date_returns_false(self):
        ev = make_evaluator()
        rule = make_rule(rule_type="OVERDUE", target_field="due_date", advance_days=0)
        assert ev.match_overdue(rule, {}) is False


class TestMatchCustomExpr:
    def test_no_expr_returns_false(self):
        ev = make_evaluator()
        rule = make_rule(rule_type="CUSTOM", condition_expr=None)
        assert ev.match_custom_expr(rule, {"x": 10}) is False

    def test_invalid_expr_returns_false(self):
        ev = make_evaluator()
        rule = make_rule(rule_type="CUSTOM", condition_expr="invalid!!!expr")
        assert ev.match_custom_expr(rule, {"x": 10}) is False
