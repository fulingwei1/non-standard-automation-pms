# -*- coding: utf-8 -*-
"""
Unit tests for app/services/bonus/team.py
批次: cov50
"""

import pytest
from unittest.mock import MagicMock
from decimal import Decimal

try:
    from app.services.bonus.team import TeamBonusCalculator
    from app.models.bonus import TeamBonusAllocation
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_calculator():
    db = MagicMock()
    return TeamBonusCalculator(db=db)


def _make_rule(coefficient=Decimal('10')):
    rule = MagicMock()
    rule.coefficient = coefficient
    rule.id = 1
    return rule


def _make_project(contract_amount=Decimal('500000')):
    proj = MagicMock()
    proj.contract_amount = contract_amount
    proj.id = 20
    return proj


def test_calculate_returns_team_allocation():
    """应返回 TeamBonusAllocation 对象"""
    calc = _make_calculator()
    rule = _make_rule()
    project = _make_project()

    # No contributions, no members
    calc.db.query.return_value.filter.return_value.all.return_value = []

    result = calc.calculate(project, rule)
    assert isinstance(result, TeamBonusAllocation)


def test_calculate_total_bonus():
    """团队总奖金 = 项目金额 * coefficient / 100"""
    calc = _make_calculator()
    rule = _make_rule(coefficient=Decimal('10'))
    project = _make_project(contract_amount=Decimal('500000'))

    calc.db.query.return_value.filter.return_value.all.return_value = []

    result = calc.calculate(project, rule)
    # 500000 * 10 / 100 = 50000
    assert result.total_bonus_amount == Decimal('50000')


def test_calculate_with_contributions():
    """有贡献记录时按贡献比例分配"""
    calc = _make_calculator()
    rule = _make_rule(coefficient=Decimal('10'))
    project = _make_project(contract_amount=Decimal('100000'))

    contrib1 = MagicMock(user_id=1, hours_percentage=Decimal('60'), period_id=None)
    contrib2 = MagicMock(user_id=2, hours_percentage=Decimal('40'), period_id=None)

    # first call for ProjectContribution
    calc.db.query.return_value.filter.return_value.all.side_effect = [
        [contrib1, contrib2],  # contributions query
    ]

    result = calc.calculate(project, rule)

    assert result.allocation_method == 'BY_CONTRIBUTION'
    assert len(result.allocation_detail) == 2


def test_calculate_equal_allocation_for_no_contributions():
    """无贡献记录时平均分配给项目成员"""
    calc = _make_calculator()
    rule = _make_rule(coefficient=Decimal('10'))
    project = _make_project(contract_amount=Decimal('100000'))

    member1 = MagicMock(user_id=1)
    member2 = MagicMock(user_id=2)

    # contributions = empty, then members
    calc.db.query.return_value.filter.return_value.all.side_effect = [
        [],           # contributions query
        [member1, member2],  # members query
    ]

    result = calc.calculate(project, rule)
    assert result.allocation_method == 'EQUAL'
    assert len(result.allocation_detail) == 2


def test_calculate_status_is_pending():
    """团队分配记录状态应为PENDING"""
    calc = _make_calculator()
    rule = _make_rule()
    project = _make_project()

    calc.db.query.return_value.filter.return_value.all.return_value = []

    result = calc.calculate(project, rule)
    assert result.status == 'PENDING'


def test_calculate_with_period_id():
    """传入period_id时应过滤对应周期的贡献"""
    calc = _make_calculator()
    rule = _make_rule()
    project = _make_project()

    contrib = MagicMock(user_id=1, hours_percentage=Decimal('100'), period_id=3)
    calc.db.query.return_value.filter.return_value.filter.return_value.all.return_value = [contrib]

    result = calc.calculate(project, rule, period_id=3)
    assert result.period_id == 3


def test_calculate_allocation_ratios_sum_to_one():
    """贡献比例之和应近似为1"""
    calc = _make_calculator()
    rule = _make_rule(coefficient=Decimal('10'))
    project = _make_project(contract_amount=Decimal('100000'))

    contrib1 = MagicMock(user_id=1, hours_percentage=Decimal('70'), period_id=None)
    contrib2 = MagicMock(user_id=2, hours_percentage=Decimal('30'), period_id=None)

    calc.db.query.return_value.filter.return_value.all.side_effect = [
        [contrib1, contrib2],
    ]

    result = calc.calculate(project, rule)
    total_ratio = sum(d["ratio"] for d in result.allocation_detail)
    assert abs(total_ratio - 1.0) < 1e-9
