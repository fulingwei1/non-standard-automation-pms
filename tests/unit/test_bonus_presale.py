# -*- coding: utf-8 -*-
"""Tests for app.services.bonus.presale"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.bonus.presale import PresaleBonusCalculator


def _make_calc():
    db = MagicMock()
    c = PresaleBonusCalculator(db)
    c.check_trigger_condition = MagicMock(return_value=True)
    c.generate_calculation_code = MagicMock(return_value="BC001")
    return c


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
    r.base_amount = kw.get("base_amount", Decimal("1000"))
    r.coefficient = kw.get("coefficient", Decimal("5"))
    return r


class TestCompletionBased:
    def test_basic_calculation(self):
        c = _make_calc()
        result = c.calculate(_make_ticket(), _make_rule(), based_on="COMPLETION")
        assert result is not None
        assert result.calculated_amount == Decimal("1000")

    def test_urgent_coefficient(self):
        c = _make_calc()
        result = c.calculate(_make_ticket(urgency="VERY_URGENT"), _make_rule(), based_on="COMPLETION")
        assert result.calculated_amount == Decimal("1300")

    def test_satisfaction_bonus(self):
        c = _make_calc()
        result = c.calculate(_make_ticket(satisfaction_score=5), _make_rule(), based_on="COMPLETION")
        assert result.calculated_amount == Decimal("1200")

    def test_low_satisfaction(self):
        c = _make_calc()
        result = c.calculate(_make_ticket(satisfaction_score=3), _make_rule(), based_on="COMPLETION")
        assert result.calculated_amount == Decimal("800")

    def test_no_assignee(self):
        c = _make_calc()
        result = c.calculate(_make_ticket(assignee_id=None), _make_rule(), based_on="COMPLETION")
        assert result is None

    def test_trigger_not_met(self):
        c = _make_calc()
        c.check_trigger_condition.return_value = False
        result = c.calculate(_make_ticket(), _make_rule(), based_on="COMPLETION")
        assert result is None


class TestWonBased:
    def test_won_opportunity(self):
        c = _make_calc()
        opp = MagicMock()
        opp.stage = "WON"
        opp.est_amount = Decimal("100000")
        c.db.query.return_value.filter.return_value.first.return_value = opp

        ticket = _make_ticket(opportunity_id=1)
        result = c.calculate(ticket, _make_rule(), based_on="WON")
        assert result is not None
        assert result.calculated_amount == Decimal("5000")

    def test_not_won(self):
        c = _make_calc()
        opp = MagicMock()
        opp.stage = "PROPOSAL"
        opp.est_amount = Decimal("100000")
        c.db.query.return_value.filter.return_value.first.return_value = opp

        ticket = _make_ticket(opportunity_id=1)
        result = c.calculate(ticket, _make_rule(), based_on="WON")
        assert result is None

    def test_invalid_based_on(self):
        c = _make_calc()
        result = c.calculate(_make_ticket(), _make_rule(), based_on="INVALID")
        assert result is None
