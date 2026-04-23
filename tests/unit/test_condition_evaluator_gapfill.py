# -*- coding: utf-8 -*-
"""ConditionEvaluator 漏行补测。"""

import builtins
import importlib
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.alert.rule_engine import condition_evaluator as ce_module
from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator


class _BrokenRule:
    def __getattr__(self, name):
        raise RuntimeError(name)



def test_module_import_fallback_when_simpleeval_missing(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "simpleeval":
            raise ImportError("missing simpleeval")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    reloaded = importlib.reload(ce_module)

    assert reloaded.simple_eval is None
    assert reloaded.InvalidExpression is Exception

    importlib.reload(ce_module)



def test_get_rule_attr_handles_attribute_error_and_invalid_threshold():
    evaluator = ConditionEvaluator(MagicMock())

    assert evaluator._get_rule_attr(_BrokenRule(), "missing", default="fallback") == "fallback"
    assert evaluator._get_numeric_threshold(SimpleNamespace(threshold_value="oops"), "threshold_value") == 0.0



def test_check_condition_dispatches_deviation_overdue_and_custom(monkeypatch):
    evaluator = ConditionEvaluator(MagicMock())
    monkeypatch.setattr(evaluator, "match_deviation", lambda *args, **kwargs: True)
    monkeypatch.setattr(evaluator, "match_overdue", lambda *args, **kwargs: True)
    monkeypatch.setattr(evaluator, "match_custom_expr", lambda *args, **kwargs: True)

    assert evaluator.check_condition(SimpleNamespace(rule_type="DEVIATION"), {}) is True
    assert evaluator.check_condition(SimpleNamespace(rule_type="OVERDUE"), {}) is True
    assert evaluator.check_condition(SimpleNamespace(rule_type="CUSTOM"), {}) is True



def test_match_threshold_unknown_operator_returns_false():
    evaluator = ConditionEvaluator(MagicMock())
    rule = SimpleNamespace(target_field="value", threshold_value=10, comparison_operator="weird")
    assert evaluator.match_threshold(rule, {"value": 20}) is False



def test_match_deviation_covers_gt_lt_lte_eq_ne_and_missing_values():
    evaluator = ConditionEvaluator(MagicMock())

    gt_rule = SimpleNamespace(target_field="actual", baseline_field="planned", threshold_value=5, comparison_operator="gt")
    assert evaluator.match_deviation(gt_rule, {"actual": 120, "planned": 100}) is True

    lt_rule = SimpleNamespace(target_field="actual", baseline_field="planned", threshold_value=5, comparison_operator="lt")
    assert evaluator.match_deviation(lt_rule, {"actual": 100, "planned": 110}) is True

    lte_rule = SimpleNamespace(target_field="actual", baseline_field="planned", threshold_value=10, comparison_operator="lte")
    assert evaluator.match_deviation(lte_rule, {"actual": 100, "planned": 110}) is True

    eq_rule = SimpleNamespace(target_field="actual", baseline_field="planned", threshold_value=10, comparison_operator="eq")
    assert evaluator.match_deviation(eq_rule, {"actual": 110, "planned": 100}) is True

    ne_rule = SimpleNamespace(target_field="actual", baseline_field="planned", threshold_value=10, comparison_operator="ne")
    assert evaluator.match_deviation(ne_rule, {"actual": 105, "planned": 100}) is True

    weird_rule = SimpleNamespace(target_field="actual", baseline_field="planned", threshold_value=10, comparison_operator="weird")
    assert evaluator.match_deviation(weird_rule, {"actual": 120, "planned": 100}) is False

    inferred_baseline_rule = SimpleNamespace(target_field="actual_cost", threshold_value=5, comparison_operator="gt")
    assert evaluator.match_deviation(inferred_baseline_rule, {"actual_cost": 100}) is False



def test_match_deviation_invalid_numeric_returns_false():
    evaluator = ConditionEvaluator(MagicMock())
    rule = SimpleNamespace(target_field="actual", baseline_field="planned", threshold_value=1, comparison_operator="gt")
    assert evaluator.match_deviation(rule, {"actual": "bad", "planned": 1}) is False



def test_match_overdue_covers_empty_invalid_string_tzinfo_and_invalid_type(monkeypatch):
    evaluator = ConditionEvaluator(MagicMock())

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            base = datetime(2026, 4, 11, 9, 0, 0)
            return base.replace(tzinfo=tz)

        @classmethod
        def fromisoformat(cls, value):
            return datetime.fromisoformat(value)

    monkeypatch.setattr(ce_module, "datetime", FixedDateTime)

    assert evaluator.match_overdue(SimpleNamespace(target_field="due_date"), {}) is False
    assert evaluator.match_overdue(SimpleNamespace(target_field="due_date"), {"due_date": "bad-date"}) is False

    tz_rule = SimpleNamespace(target_field="due_date", advance_days="bad")
    due = FixedDateTime(2026, 4, 11, 8, 0, 0, tzinfo=timezone.utc)
    assert evaluator.match_overdue(tz_rule, {"due_date": due}) is True

    assert evaluator.match_overdue(SimpleNamespace(target_field="due_date"), {"due_date": 123}) is False



def test_match_custom_expr_covers_empty_simpleeval_success_eval_fallback_and_invalid_expression(monkeypatch):
    evaluator = ConditionEvaluator(MagicMock())

    assert evaluator.match_custom_expr(SimpleNamespace(), {"value": 1}) is False

    monkeypatch.setattr(ce_module, "simple_eval", lambda expr, names: names["value"] > 10)
    assert evaluator.match_custom_expr(SimpleNamespace(custom_expression="value > 10"), {"value": 11}) is True

    monkeypatch.setattr(ce_module, "simple_eval", None)
    assert evaluator.match_custom_expr(SimpleNamespace(custom_expression="value + bonus > 10"), {"value": 8}, {"bonus": 5}) is True

    class MyInvalidExpression(Exception):
        pass

    def raising_simple_eval(expr, names):
        raise MyInvalidExpression("boom")

    monkeypatch.setattr(ce_module, "InvalidExpression", MyInvalidExpression)
    monkeypatch.setattr(ce_module, "simple_eval", raising_simple_eval)
    assert evaluator.match_custom_expr(SimpleNamespace(custom_expression="value > 0"), {"value": 1}) is False
