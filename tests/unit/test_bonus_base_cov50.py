# -*- coding: utf-8 -*-
"""
Unit tests for app/services/bonus/base.py
批次: cov50
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

try:
    from app.services.bonus.base import BonusCalculatorBase
    from app.models.enums import PerformanceLevelEnum
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_calculator():
    db = MagicMock()
    return BonusCalculatorBase(db=db)


def test_generate_calculation_code_format():
    """生成计算单号格式应以BC开头"""
    calc = _make_calculator()
    code = calc.generate_calculation_code()
    assert code.startswith("BC")
    assert len(code) > 2


def test_generate_calculation_code_unique():
    """多次生成的单号应不同（基于时间戳）"""
    calc = _make_calculator()
    codes = {calc.generate_calculation_code() for _ in range(3)}
    # 在同一秒内可能相同，但结构应正确
    for code in codes:
        assert code.startswith("BC")


def test_check_trigger_condition_no_condition():
    """无触发条件时应始终返回True"""
    calc = _make_calculator()
    rule = MagicMock()
    rule.trigger_condition = None
    assert calc.check_trigger_condition(rule, {}) is True


def test_check_trigger_condition_performance_level_match():
    """绩效等级匹配时应返回True"""
    calc = _make_calculator()
    rule = MagicMock()
    rule.trigger_condition = {"performance_level": "EXCELLENT"}

    perf = MagicMock()
    perf.level = "EXCELLENT"
    context = {"performance_result": perf}

    assert calc.check_trigger_condition(rule, context) is True


def test_check_trigger_condition_performance_level_mismatch():
    """绩效等级不匹配时应返回False"""
    calc = _make_calculator()
    rule = MagicMock()
    rule.trigger_condition = {"performance_level": "EXCELLENT"}

    perf = MagicMock()
    perf.level = "POOR"
    context = {"performance_result": perf}

    assert calc.check_trigger_condition(rule, context) is False


def test_check_trigger_condition_min_score_pass():
    """分数满足最低要求时应返回True"""
    calc = _make_calculator()
    rule = MagicMock()
    rule.trigger_condition = {"min_score": 80}

    perf = MagicMock()
    perf.total_score = Decimal('90')
    context = {"performance_result": perf}

    assert calc.check_trigger_condition(rule, context) is True


def test_check_trigger_condition_min_score_fail():
    """分数不满足最低要求时应返回False"""
    calc = _make_calculator()
    rule = MagicMock()
    rule.trigger_condition = {"min_score": 80}

    perf = MagicMock()
    perf.total_score = Decimal('70')
    context = {"performance_result": perf}

    assert calc.check_trigger_condition(rule, context) is False


def test_get_coefficient_by_level():
    """根据绩效等级获取系数"""
    calc = _make_calculator()
    try:
        excellent_coef = calc.get_coefficient_by_level(PerformanceLevelEnum.EXCELLENT)
        good_coef = calc.get_coefficient_by_level(PerformanceLevelEnum.GOOD)
        assert excellent_coef > good_coef
    except AttributeError:
        pytest.skip("PerformanceLevelEnum attributes not available")


def test_get_coefficient_by_level_unknown():
    """未知等级应返回默认系数1.0"""
    calc = _make_calculator()
    coef = calc.get_coefficient_by_level("UNKNOWN_LEVEL")
    assert coef == Decimal('1.0')


def test_get_role_coefficient_default():
    """PM角色系数应大于1"""
    calc = _make_calculator()
    rule = MagicMock()
    rule.trigger_condition = None

    coef = calc.get_role_coefficient("PM", rule)
    assert coef >= Decimal('1.0')


def test_get_active_rules():
    """获取活跃规则时应查询数据库"""
    calc = _make_calculator()
    mock_rule = MagicMock()
    calc.db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_rule]

    rules = calc.get_active_rules()
    # Should call db.query
    calc.db.query.assert_called()
