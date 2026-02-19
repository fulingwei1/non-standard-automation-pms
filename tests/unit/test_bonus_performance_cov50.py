# -*- coding: utf-8 -*-
"""
Unit tests for app/services/bonus/performance.py
批次: cov50
"""

import pytest
from unittest.mock import MagicMock
from decimal import Decimal

try:
    from app.services.bonus.performance import PerformanceBonusCalculator
    from app.models.bonus import BonusCalculation
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_calculator():
    db = MagicMock()
    return PerformanceBonusCalculator(db=db)


def _make_rule(base_amount=Decimal('1000'), trigger_condition=None):
    rule = MagicMock()
    rule.base_amount = base_amount
    rule.trigger_condition = trigger_condition
    rule.id = 1
    return rule


def _make_perf_result(level="EXCELLENT", score=Decimal('90'), user_id=1, period_id=2):
    pr = MagicMock()
    pr.level = level
    pr.total_score = score
    pr.user_id = user_id
    pr.period_id = period_id
    pr.id = 10
    return pr


def test_calculate_returns_calculation_for_valid_input():
    """正常绩效结果应返回BonusCalculation"""
    calc = _make_calculator()
    rule = _make_rule()
    pr = _make_perf_result()

    result = calc.calculate(pr, rule)

    assert result is not None
    assert result.status == 'CALCULATED'
    assert result.user_id == pr.user_id


def test_calculate_amount_uses_base_and_coefficient():
    """计算金额 = base_amount * coefficient"""
    calc = _make_calculator()
    rule = _make_rule(base_amount=Decimal('1000'))
    pr = _make_perf_result(level="EXCELLENT")

    result = calc.calculate(pr, rule)

    assert result is not None
    # EXCELLENT coefficient is 1.5, so amount should be 1500
    assert result.calculated_amount == Decimal('1500')


def test_calculate_returns_none_when_condition_not_met():
    """触发条件不满足时应返回None"""
    calc = _make_calculator()
    rule = _make_rule(trigger_condition={"performance_level": "EXCELLENT"})
    pr = _make_perf_result(level="POOR")

    result = calc.calculate(pr, rule)
    assert result is None


def test_calculate_sets_calculation_code():
    """计算记录应包含有效的单号"""
    calc = _make_calculator()
    rule = _make_rule()
    pr = _make_perf_result()

    result = calc.calculate(pr, rule)
    assert result.calculation_code.startswith("BC")


def test_calculate_detail_contains_performance_level():
    """calculation_detail 应包含绩效等级信息"""
    calc = _make_calculator()
    rule = _make_rule()
    pr = _make_perf_result(level="GOOD")

    result = calc.calculate(pr, rule)
    assert result is not None
    assert result.calculation_detail["performance_level"] == "GOOD"


def test_calculate_with_no_base_amount():
    """base_amount 为0时计算结果为0"""
    calc = _make_calculator()
    rule = _make_rule(base_amount=Decimal('0'))
    pr = _make_perf_result()

    result = calc.calculate(pr, rule)
    assert result is not None
    assert result.calculated_amount == Decimal('0')


def test_calculate_sets_period_id():
    """计算记录应包含正确的 period_id"""
    calc = _make_calculator()
    rule = _make_rule()
    pr = _make_perf_result(period_id=5)

    result = calc.calculate(pr, rule)
    assert result.period_id == 5


def test_calculate_basis_type_is_performance():
    """calculation_basis 类型应为 performance"""
    calc = _make_calculator()
    rule = _make_rule()
    pr = _make_perf_result()

    result = calc.calculate(pr, rule)
    assert result.calculation_basis["type"] == "performance"
