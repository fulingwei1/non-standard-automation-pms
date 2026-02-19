# -*- coding: utf-8 -*-
"""Unit tests for app/services/bonus/performance.py - batch 41"""
import pytest

pytest.importorskip("app.services.bonus.performance")

from unittest.mock import MagicMock, patch
from decimal import Decimal


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def calculator(db):
    from app.services.bonus.performance import PerformanceBonusCalculator
    return PerformanceBonusCalculator(db)


def test_instantiation(calculator):
    assert calculator is not None


def test_calculate_returns_none_if_condition_not_met(calculator):
    rule = MagicMock()
    rule.trigger_condition = {"performance_level": "S"}
    perf = MagicMock()
    perf.level = "A"
    result = calculator.calculate(perf, rule)
    assert result is None


def test_calculate_returns_bonus_calculation(calculator):
    rule = MagicMock()
    rule.trigger_condition = None
    rule.id = 1
    rule.base_amount = Decimal("1000")
    perf = MagicMock()
    perf.level = "EXCELLENT"
    perf.period_id = 1
    perf.user_id = 5
    perf.id = 10
    perf.total_score = Decimal("95")

    with patch.object(calculator, "get_coefficient_by_level", return_value=Decimal("1.5")), \
         patch("app.services.bonus.performance.BonusCalculation") as MockCalc:
        MockCalc.return_value = MagicMock()
        result = calculator.calculate(perf, rule)
        assert result is not None
        MockCalc.assert_called_once()


def test_calculate_amount_correctly(calculator):
    rule = MagicMock()
    rule.trigger_condition = None
    rule.id = 2
    rule.base_amount = Decimal("2000")
    perf = MagicMock()
    perf.level = "GOOD"
    perf.period_id = 2
    perf.user_id = 6
    perf.id = 20
    perf.total_score = Decimal("88")

    captured = {}

    with patch.object(calculator, "get_coefficient_by_level", return_value=Decimal("1.2")), \
         patch("app.services.bonus.performance.BonusCalculation") as MockCalc:
        def capture(**kwargs):
            captured.update(kwargs)
            return MagicMock()
        MockCalc.side_effect = capture
        calculator.calculate(perf, rule)
        assert captured.get("calculated_amount") == Decimal("2400")


def test_calculate_detail_includes_level(calculator):
    rule = MagicMock()
    rule.trigger_condition = None
    rule.id = 3
    rule.base_amount = Decimal("500")
    perf = MagicMock()
    perf.level = "QUALIFIED"
    perf.period_id = 3
    perf.user_id = 7
    perf.id = 30
    perf.total_score = Decimal("75")

    with patch.object(calculator, "get_coefficient_by_level", return_value=Decimal("1.0")), \
         patch("app.services.bonus.performance.BonusCalculation") as MockCalc:
        MockCalc.return_value = MagicMock()
        calculator.calculate(perf, rule)
        kwargs = MockCalc.call_args[1]
        assert kwargs["calculation_detail"]["performance_level"] == "QUALIFIED"


def test_calculate_status_is_calculated(calculator):
    rule = MagicMock()
    rule.trigger_condition = None
    rule.id = 4
    rule.base_amount = Decimal("100")
    perf = MagicMock()
    perf.level = "GOOD"
    perf.period_id = 1
    perf.user_id = 1
    perf.id = 1
    perf.total_score = Decimal("80")

    with patch.object(calculator, "get_coefficient_by_level", return_value=Decimal("1.2")), \
         patch("app.services.bonus.performance.BonusCalculation") as MockCalc:
        MockCalc.return_value = MagicMock()
        calculator.calculate(perf, rule)
        kwargs = MockCalc.call_args[1]
        assert kwargs["status"] == "CALCULATED"
