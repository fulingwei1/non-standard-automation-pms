# -*- coding: utf-8 -*-
"""预警规则引擎服务单元测试"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.models.enums import AlertLevelEnum


class TestAlertRuleEngineBase:
    @pytest.fixture
    def engine_base(self):
        from app.services.alert.rule_engine.base import AlertRuleEngineBase

        return AlertRuleEngineBase()

    def test_level_priority_info(self, engine_base):
        assert engine_base.level_priority(AlertLevelEnum.INFO.value) == 1

    def test_level_priority_warning(self, engine_base):
        assert engine_base.level_priority(AlertLevelEnum.WARNING.value) == 2

    def test_level_priority_critical(self, engine_base):
        assert engine_base.level_priority(AlertLevelEnum.CRITICAL.value) == 3

    def test_level_priority_urgent(self, engine_base):
        assert engine_base.level_priority(AlertLevelEnum.URGENT.value) == 4

    def test_level_priority_unknown(self, engine_base):
        assert engine_base.level_priority("UNKNOWN") == 0

    def test_get_field_value_simple(self, engine_base):
        target_data = {"value": 100, "name": "测试"}
        assert engine_base.get_field_value("value", target_data) == 100
        assert engine_base.get_field_value("name", target_data) == "测试"

    def test_get_field_value_nested(self, engine_base):
        target_data = {"project": {"progress": 80, "status": "进行中"}}
        assert engine_base.get_field_value("project.progress", target_data) == 80
        assert engine_base.get_field_value("project.status", target_data) == "进行中"

    def test_get_field_value_from_context(self, engine_base):
        target_data = {"value": 100}
        context = {"extra_value": 200}
        assert engine_base.get_field_value("extra_value", target_data, context) == 200

    def test_get_field_value_priority(self, engine_base):
        target_data = {"value": 100}
        context = {"value": 200}
        assert engine_base.get_field_value("value", target_data, context) == 100

    def test_get_field_value_not_found(self, engine_base):
        assert engine_base.get_field_value("not_exist", {"value": 100}) is None

    def test_get_field_value_none_data(self, engine_base):
        assert engine_base.get_field_value("value", {}) is None

    def test_get_nested_value_with_object(self, engine_base):
        class MockObj:
            def __init__(self):
                self.value = 42

        target_data = {"obj": MockObj()}
        assert engine_base.get_field_value("obj.value", target_data) == 42


class TestConditionEvaluator:
    @pytest.fixture
    def evaluator(self):
        from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

        return ConditionEvaluator()

    @pytest.fixture
    def mock_rule(self):
        rule = MagicMock()
        rule.is_enabled = True
        rule.threshold_value = 100
        rule.condition_operator = "GT"
        rule.target_field = "value"
        return rule

    def test_match_threshold_gt(self, evaluator, mock_rule):
        mock_rule.rule_type = "THRESHOLD"
        mock_rule.condition_operator = "GT"
        assert evaluator.match_threshold(mock_rule, {"value": 101}) is True
        assert evaluator.match_threshold(mock_rule, {"value": 100}) is False

    def test_match_threshold_gte(self, evaluator, mock_rule):
        mock_rule.condition_operator = "GTE"
        assert evaluator.match_threshold(mock_rule, {"value": 100}) is True

    def test_match_threshold_lt(self, evaluator, mock_rule):
        mock_rule.condition_operator = "LT"
        assert evaluator.match_threshold(mock_rule, {"value": 99}) is True

    def test_match_threshold_lte(self, evaluator, mock_rule):
        mock_rule.condition_operator = "LTE"
        assert evaluator.match_threshold(mock_rule, {"value": 100}) is True

    def test_match_threshold_eq(self, evaluator, mock_rule):
        mock_rule.condition_operator = "EQ"
        assert evaluator.match_threshold(mock_rule, {"value": 100}) is True

    def test_match_threshold_invalid_operator(self, evaluator, mock_rule):
        mock_rule.condition_operator = "INVALID"
        assert evaluator.match_threshold(mock_rule, {"value": 100}) is False

    def test_match_threshold_none_value(self, evaluator, mock_rule):
        assert evaluator.match_threshold(mock_rule, {"value": None}) is False
        assert evaluator.match_threshold(mock_rule, {}) is False

    def test_match_threshold_invalid_value(self, evaluator, mock_rule):
        assert evaluator.match_threshold(mock_rule, {"value": "abc"}) is False

    def test_match_deviation_gt(self, evaluator, mock_rule):
        mock_rule.rule_type = "DEVIATION"
        mock_rule.condition_operator = "GT"
        mock_rule.threshold_value = 10
        mock_rule.target_field = "actual_cost"
        assert evaluator.match_deviation(mock_rule, {"actual_cost": 120, "planned_cost": 100}) is True

    def test_match_deviation_within_threshold(self, evaluator, mock_rule):
        mock_rule.rule_type = "DEVIATION"
        mock_rule.condition_operator = "GT"
        mock_rule.threshold_value = 10
        mock_rule.target_field = "actual_cost"
        assert evaluator.match_deviation(mock_rule, {"actual_cost": 105, "planned_cost": 100}) is False

    def test_match_deviation_missing_values(self, evaluator, mock_rule):
        mock_rule.target_field = "actual_value"
        assert evaluator.match_deviation(mock_rule, {"actual_value": 100}) is False
        assert evaluator.match_deviation(mock_rule, {"planned_value": 100}) is False

    def test_match_overdue_past_due(self, evaluator, mock_rule):
        mock_rule.rule_type = "OVERDUE"
        mock_rule.target_field = "due_date"
        mock_rule.advance_days = 0
        yesterday = datetime.now() - timedelta(days=1)
        assert evaluator.match_overdue(mock_rule, {"due_date": yesterday.isoformat()}) is True

    def test_match_overdue_future_due(self, evaluator, mock_rule):
        mock_rule.rule_type = "OVERDUE"
        mock_rule.target_field = "due_date"
        mock_rule.advance_days = 0
        tomorrow = datetime.now() + timedelta(days=1)
        assert evaluator.match_overdue(mock_rule, {"due_date": tomorrow.isoformat()}) is False
