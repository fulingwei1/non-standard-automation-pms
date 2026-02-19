# -*- coding: utf-8 -*-
"""Unit tests for app/services/bonus/base.py - batch 41"""
import pytest

pytest.importorskip("app.services.bonus.base")

from unittest.mock import MagicMock, patch
from decimal import Decimal


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def calculator(db):
    from app.services.bonus.base import BonusCalculatorBase
    return BonusCalculatorBase(db)


def test_generate_calculation_code(calculator):
    code = calculator.generate_calculation_code()
    assert code.startswith("BC")
    assert len(code) > 5


def test_check_trigger_condition_no_condition(calculator):
    rule = MagicMock()
    rule.trigger_condition = None
    result = calculator.check_trigger_condition(rule, {})
    assert result is True


def test_check_trigger_condition_performance_level_match(calculator):
    rule = MagicMock()
    rule.trigger_condition = {"performance_level": "A"}
    perf = MagicMock()
    perf.level = "A"
    result = calculator.check_trigger_condition(rule, {"performance_result": perf})
    assert result is True


def test_check_trigger_condition_performance_level_mismatch(calculator):
    rule = MagicMock()
    rule.trigger_condition = {"performance_level": "A"}
    perf = MagicMock()
    perf.level = "B"
    result = calculator.check_trigger_condition(rule, {"performance_result": perf})
    assert result is False


def test_get_coefficient_by_level_excellent(calculator):
    with patch("app.services.bonus.base.PerformanceLevelEnum") as MockEnum:
        MockEnum.EXCELLENT = "EXCELLENT"
        MockEnum.GOOD = "GOOD"
        MockEnum.QUALIFIED = "QUALIFIED"
        MockEnum.NEEDS_IMPROVEMENT = "NEEDS_IMPROVEMENT"
        MockEnum.AVERAGE = "AVERAGE"
        MockEnum.POOR = "POOR"
        from app.services.bonus.base import BonusCalculatorBase
        calc = BonusCalculatorBase(MagicMock())
        result = calc.get_coefficient_by_level("EXCELLENT")
        assert result == Decimal("1.5")


def test_get_role_coefficient_pm(calculator):
    rule = MagicMock()
    rule.trigger_condition = {}
    result = calculator.get_role_coefficient("PM", rule)
    assert result == Decimal("1.5")


def test_get_role_coefficient_from_rule_config(calculator):
    rule = MagicMock()
    rule.trigger_condition = {"role_coefficients": {"PM": 2.0}}
    result = calculator.get_role_coefficient("PM", rule)
    assert result == Decimal("2.0")


def test_get_active_rules_returns_list(calculator, db):
    db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
    from app.services.bonus.base import BonusCalculatorBase
    # Just ensure no error
    result = calculator.get_active_rules()
    assert isinstance(result, list)
