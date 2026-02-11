# -*- coding: utf-8 -*-
"""Tests for alert_rule_engine/condition_evaluator.py"""
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from app.services.alert_rule_engine.condition_evaluator import ConditionEvaluator


class TestCheckCondition:
    def setup_method(self):
        self.evaluator = ConditionEvaluator.__new__(ConditionEvaluator)

    def test_threshold_type(self):
        rule = MagicMock(rule_type="THRESHOLD", target_field="value",
                         threshold_value=10, condition_operator="GT")
        with patch.object(self.evaluator, 'get_field_value', return_value=15):
            assert self.evaluator.check_condition(rule, {}) is True

    def test_unknown_type(self):
        rule = MagicMock(rule_type="UNKNOWN")
        assert self.evaluator.check_condition(rule, {}) is False


class TestMatchThreshold:
    def setup_method(self):
        self.evaluator = ConditionEvaluator.__new__(ConditionEvaluator)

    def _rule(self, op="GT", threshold=10, field="value"):
        return MagicMock(target_field=field, threshold_value=threshold, condition_operator=op)

    def test_gt(self):
        with patch.object(self.evaluator, 'get_field_value', return_value=15):
            assert self.evaluator.match_threshold(self._rule("GT", 10), {}) is True

    def test_lt(self):
        with patch.object(self.evaluator, 'get_field_value', return_value=5):
            assert self.evaluator.match_threshold(self._rule("LT", 10), {}) is True

    def test_eq(self):
        with patch.object(self.evaluator, 'get_field_value', return_value=10):
            assert self.evaluator.match_threshold(self._rule("EQ", 10), {}) is True

    def test_gte(self):
        with patch.object(self.evaluator, 'get_field_value', return_value=10):
            assert self.evaluator.match_threshold(self._rule("GTE", 10), {}) is True

    def test_lte(self):
        with patch.object(self.evaluator, 'get_field_value', return_value=10):
            assert self.evaluator.match_threshold(self._rule("LTE", 10), {}) is True

    def test_none_value(self):
        with patch.object(self.evaluator, 'get_field_value', return_value=None):
            assert self.evaluator.match_threshold(self._rule(), {}) is False

    def test_invalid_value(self):
        with patch.object(self.evaluator, 'get_field_value', return_value="abc"):
            assert self.evaluator.match_threshold(self._rule(), {}) is False


class TestMatchDeviation:
    def setup_method(self):
        self.evaluator = ConditionEvaluator.__new__(ConditionEvaluator)

    def test_deviation_gt(self):
        rule = MagicMock(target_field="actual_value", threshold_value=5, condition_operator="GT")
        with patch.object(self.evaluator, 'get_field_value', side_effect=[20, 10]):
            assert self.evaluator.match_deviation(rule, {}) is True

    def test_none_values(self):
        rule = MagicMock(target_field="actual_value", threshold_value=5, condition_operator="GT")
        with patch.object(self.evaluator, 'get_field_value', side_effect=[None, 10]):
            assert self.evaluator.match_deviation(rule, {}) is False


class TestMatchOverdue:
    def setup_method(self):
        self.evaluator = ConditionEvaluator.__new__(ConditionEvaluator)

    def test_overdue(self):
        rule = MagicMock(target_field="due_date", advance_days=0)
        past = datetime.now() - timedelta(days=1)
        with patch.object(self.evaluator, 'get_field_value', return_value=past):
            assert self.evaluator.match_overdue(rule, {}) is True

    def test_not_overdue(self):
        rule = MagicMock(target_field="due_date", advance_days=0)
        future = datetime.now() + timedelta(days=10)
        with patch.object(self.evaluator, 'get_field_value', return_value=future):
            assert self.evaluator.match_overdue(rule, {}) is False

    def test_string_date(self):
        rule = MagicMock(target_field="due_date", advance_days=0)
        past = (datetime.now() - timedelta(days=1)).isoformat()
        with patch.object(self.evaluator, 'get_field_value', return_value=past):
            assert self.evaluator.match_overdue(rule, {}) is True

    def test_no_due_date(self):
        rule = MagicMock(target_field="due_date", advance_days=0)
        with patch.object(self.evaluator, 'get_field_value', return_value=None):
            assert self.evaluator.match_overdue(rule, {}) is False


class TestMatchCustomExpr:
    def setup_method(self):
        self.evaluator = ConditionEvaluator.__new__(ConditionEvaluator)

    def test_no_expression(self):
        rule = MagicMock(condition_expr=None)
        assert self.evaluator.match_custom_expr(rule, {}) is False

    @patch("app.services.alert_rule_engine.condition_evaluator.simple_eval")
    def test_valid_expression(self, mock_eval):
        mock_eval.return_value = True
        rule = MagicMock(condition_expr="value > 10")
        result = self.evaluator.match_custom_expr(rule, {"value": 15})
        assert result is True

    @patch("app.services.alert_rule_engine.condition_evaluator.simple_eval", None)
    def test_no_simpleeval(self):
        rule = MagicMock(condition_expr="value > 10")
        result = self.evaluator.match_custom_expr(rule, {"value": 15})
        assert result is False
