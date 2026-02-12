# -*- coding: utf-8 -*-
"""售前奖金计算器 单元测试"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.bonus.presale import PresaleBonusCalculator


def _make_calc():
    db = MagicMock()
    with patch.object(PresaleBonusCalculator, "__init__", lambda self, db: None):
        calc = PresaleBonusCalculator(db)
    calc.db = db
    calc.check_trigger_condition = MagicMock(return_value=True)
    calc.generate_calculation_code = MagicMock(return_value="BC001")
    return calc


def _make_ticket(**kw):
    t = MagicMock()
    t.id = kw.get("id", 1)
    t.ticket_no = kw.get("ticket_no", "T001")
    t.ticket_type = kw.get("ticket_type", "TECH")
    t.assignee_id = kw.get("assignee_id", 10)
    t.urgency = kw.get("urgency", "NORMAL")
    t.satisfaction_score = kw.get("satisfaction_score", None)
    t.opportunity_id = kw.get("opportunity_id", None)
    t.project_id = kw.get("project_id", None)
    return t


def _make_rule(**kw):
    r = MagicMock()
    r.id = kw.get("id", 1)
    r.base_amount = kw.get("base_amount", Decimal("100"))
    r.coefficient = kw.get("coefficient", Decimal("5"))
    return r


class TestCompletionBased:
    def test_basic_calculation(self):
        calc = _make_calc()
        ticket = _make_ticket()
        rule = _make_rule(base_amount=Decimal("100"))
        with patch("app.services.bonus.presale.BonusCalculation") as MockBC:
            MockBC.return_value = MagicMock()
            result = calc.calculate(ticket, rule, based_on="COMPLETION")
        assert result is not None

    def test_urgent_coefficient(self):
        calc = _make_calc()
        ticket = _make_ticket(urgency="VERY_URGENT")
        rule = _make_rule(base_amount=Decimal("100"))
        with patch("app.services.bonus.presale.BonusCalculation") as MockBC:
            instance = MagicMock()
            MockBC.return_value = instance
            result = calc.calculate(ticket, rule, based_on="COMPLETION")
            # Check that calculated_amount uses 1.3 coefficient
            call_kwargs = MockBC.call_args[1]
            assert call_kwargs["calculated_amount"] == Decimal("130.0")

    def test_high_satisfaction(self):
        calc = _make_calc()
        ticket = _make_ticket(satisfaction_score=5)
        rule = _make_rule(base_amount=Decimal("100"))
        with patch("app.services.bonus.presale.BonusCalculation") as MockBC:
            MockBC.return_value = MagicMock()
            result = calc.calculate(ticket, rule, based_on="COMPLETION")
            call_kwargs = MockBC.call_args[1]
            assert call_kwargs["calculated_amount"] == Decimal("120.0")

    def test_no_assignee_returns_none(self):
        calc = _make_calc()
        ticket = _make_ticket(assignee_id=None)
        rule = _make_rule()
        result = calc.calculate(ticket, rule, based_on="COMPLETION")
        assert result is None

    def test_trigger_not_met(self):
        calc = _make_calc()
        calc.check_trigger_condition.return_value = False
        ticket = _make_ticket()
        rule = _make_rule()
        result = calc.calculate(ticket, rule, based_on="COMPLETION")
        assert result is None


class TestWonBased:
    def test_not_won_returns_none(self):
        calc = _make_calc()
        ticket = _make_ticket(opportunity_id=1)
        rule = _make_rule()
        opp = MagicMock()
        opp.stage = "PROPOSAL"
        calc.db.query.return_value.filter.return_value.first.return_value = opp
        result = calc.calculate(ticket, rule, based_on="WON")
        assert result is None

    def test_invalid_based_on(self):
        calc = _make_calc()
        ticket = _make_ticket()
        rule = _make_rule()
        result = calc.calculate(ticket, rule, based_on="INVALID")
        assert result is None
