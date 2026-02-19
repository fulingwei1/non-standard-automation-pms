# -*- coding: utf-8 -*-
"""Unit tests for app/services/bonus/team.py - batch 41"""
import pytest

pytest.importorskip("app.services.bonus.team")

from unittest.mock import MagicMock, patch
from decimal import Decimal


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def calculator(db):
    from app.services.bonus.team import TeamBonusCalculator
    return TeamBonusCalculator(db)


def test_instantiation(calculator):
    assert calculator is not None


def test_calculate_no_contributions_equal_distribution(calculator, db):
    project = MagicMock()
    project.id = 1
    project.contract_amount = Decimal("100000")
    rule = MagicMock()
    rule.coefficient = Decimal("5")
    # No contributions
    db.query.return_value.filter.return_value.all.return_value = []
    # Members for equal distribution
    member = MagicMock()
    member.user_id = 10

    call_count = [0]
    def query_side_effect(*args, **kwargs):
        call_count[0] += 1
        q = MagicMock()
        if call_count[0] == 1:
            # contributions
            q.filter.return_value.all.return_value = []
        else:
            # members
            q.filter.return_value.all.return_value = [member]
        return q

    db.query.side_effect = query_side_effect

    with patch("app.services.bonus.team.TeamBonusAllocation") as MockAlloc:
        MockAlloc.return_value = MagicMock()
        result = calculator.calculate(project, rule)
        kwargs = MockAlloc.call_args[1]
        assert kwargs["allocation_method"] == "EQUAL"


def test_calculate_with_contributions(calculator, db):
    project = MagicMock()
    project.id = 1
    project.contract_amount = Decimal("50000")
    rule = MagicMock()
    rule.coefficient = Decimal("4")
    contrib1 = MagicMock()
    contrib1.user_id = 1
    contrib1.hours_percentage = Decimal("60")
    contrib2 = MagicMock()
    contrib2.user_id = 2
    contrib2.hours_percentage = Decimal("40")
    db.query.return_value.filter.return_value.all.return_value = [contrib1, contrib2]

    with patch("app.services.bonus.team.TeamBonusAllocation") as MockAlloc:
        MockAlloc.return_value = MagicMock()
        result = calculator.calculate(project, rule)
        kwargs = MockAlloc.call_args[1]
        assert kwargs["allocation_method"] == "BY_CONTRIBUTION"
        assert len(kwargs["allocation_detail"]) == 2


def test_calculate_total_bonus_amount(calculator, db):
    project = MagicMock()
    project.id = 1
    project.contract_amount = Decimal("100000")
    rule = MagicMock()
    rule.coefficient = Decimal("5")  # 5%
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.side_effect = None
    db.query.return_value.filter.return_value.all.return_value = []

    call_count = [0]
    def query_side(*args, **kwargs):
        call_count[0] += 1
        q = MagicMock()
        q.filter.return_value.all.return_value = []
        return q

    db.query.side_effect = query_side

    with patch("app.services.bonus.team.TeamBonusAllocation") as MockAlloc:
        MockAlloc.return_value = MagicMock()
        calculator.calculate(project, rule)
        kwargs = MockAlloc.call_args[1]
        # 100000 * 5 / 100 = 5000
        assert kwargs["total_bonus_amount"] == Decimal("5000")


def test_calculate_with_period_id(calculator, db):
    project = MagicMock()
    project.id = 2
    project.contract_amount = Decimal("20000")
    rule = MagicMock()
    rule.coefficient = Decimal("10")
    db.query.return_value.filter.return_value.all.return_value = []

    call_count = [0]
    def query_side(*args, **kwargs):
        call_count[0] += 1
        q = MagicMock()
        q.filter.return_value.all.return_value = []
        return q

    db.query.side_effect = query_side

    with patch("app.services.bonus.team.TeamBonusAllocation") as MockAlloc:
        MockAlloc.return_value = MagicMock()
        result = calculator.calculate(project, rule, period_id=5)
        kwargs = MockAlloc.call_args[1]
        assert kwargs["period_id"] == 5


def test_calculate_allocation_status_pending(calculator, db):
    project = MagicMock()
    project.id = 1
    project.contract_amount = Decimal("10000")
    rule = MagicMock()
    rule.coefficient = Decimal("2")
    db.query.side_effect = lambda *a, **kw: MagicMock(
        filter=lambda *a, **kw: MagicMock(all=lambda: [])
    )

    with patch("app.services.bonus.team.TeamBonusAllocation") as MockAlloc:
        MockAlloc.return_value = MagicMock()
        calculator.calculate(project, rule)
        kwargs = MockAlloc.call_args[1]
        assert kwargs["status"] == "PENDING"
