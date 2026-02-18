# -*- coding: utf-8 -*-
"""第二十批 - presale (bonus/presale) 单元测试"""
import pytest
pytest.importorskip("app.services.bonus.presale")

from decimal import Decimal
from unittest.mock import MagicMock, patch
from app.services.bonus.presale import PresaleBonusCalculator


def make_db():
    return MagicMock()


def make_calculator(db=None):
    if db is None:
        db = make_db()
    return PresaleBonusCalculator(db), db


def make_ticket(
    id=1, ticket_no="PRE-001", assignee_id=10, urgency="NORMAL",
    satisfaction_score=4, opportunity_id=None, project_id=None,
    ticket_type="DEMO"
):
    t = MagicMock()
    t.id = id
    t.ticket_no = ticket_no
    t.assignee_id = assignee_id
    t.urgency = urgency
    t.satisfaction_score = satisfaction_score
    t.opportunity_id = opportunity_id
    t.project_id = project_id
    t.ticket_type = ticket_type
    return t


def make_rule(
    id=1, base_amount=Decimal("500"), coefficient=Decimal("2")
):
    r = MagicMock()
    r.id = id
    r.base_amount = base_amount
    r.coefficient = coefficient
    return r


class TestPresaleBonusCalculatorInit:
    def test_init(self):
        calc, db = make_calculator()
        assert calc.db is db


class TestCalculateCompletion:
    def test_trigger_not_met_returns_none(self):
        calc, db = make_calculator()
        ticket = make_ticket()
        rule = make_rule()
        with patch.object(calc, 'check_trigger_condition', return_value=False):
            result = calc.calculate(ticket, rule, based_on='COMPLETION')
            assert result is None

    def test_no_assignee_returns_none(self):
        calc, db = make_calculator()
        ticket = make_ticket(assignee_id=None)
        rule = make_rule()
        with patch.object(calc, 'check_trigger_condition', return_value=True):
            result = calc.calculate(ticket, rule, based_on='COMPLETION')
            assert result is None

    def test_completion_normal_urgency(self):
        calc, db = make_calculator()
        ticket = make_ticket(urgency='NORMAL', satisfaction_score=4)
        rule = make_rule(base_amount=Decimal('1000'))
        with patch.object(calc, 'check_trigger_condition', return_value=True):
            with patch.object(calc, 'generate_calculation_code', return_value='CALC-001'):
                with patch('app.services.bonus.presale.BonusCalculation') as MockCalc:
                    mock_bc = MagicMock()
                    MockCalc.return_value = mock_bc
                    result = calc.calculate(ticket, rule, based_on='COMPLETION')
                    assert result is mock_bc
                    call_kwargs = MockCalc.call_args[1]
                    # Normal urgency * normal satisfaction = 1000 * 1.0 * 1.0 = 1000
                    assert call_kwargs['calculated_amount'] == Decimal('1000.0')

    def test_completion_very_urgent_urgency(self):
        calc, db = make_calculator()
        ticket = make_ticket(urgency='VERY_URGENT', satisfaction_score=5)
        rule = make_rule(base_amount=Decimal('1000'))
        with patch.object(calc, 'check_trigger_condition', return_value=True):
            with patch.object(calc, 'generate_calculation_code', return_value='CALC-002'):
                with patch('app.services.bonus.presale.BonusCalculation') as MockCalc:
                    MockCalc.return_value = MagicMock()
                    result = calc.calculate(ticket, rule, based_on='COMPLETION')
                    call_kwargs = MockCalc.call_args[1]
                    # 1000 * 1.3 * 1.2 = 1560
                    assert call_kwargs['calculated_amount'] == Decimal('1560.00')

    def test_completion_low_satisfaction(self):
        calc, db = make_calculator()
        ticket = make_ticket(urgency='NORMAL', satisfaction_score=2)
        rule = make_rule(base_amount=Decimal('1000'))
        with patch.object(calc, 'check_trigger_condition', return_value=True):
            with patch.object(calc, 'generate_calculation_code', return_value='CALC-003'):
                with patch('app.services.bonus.presale.BonusCalculation') as MockCalc:
                    MockCalc.return_value = MagicMock()
                    result = calc.calculate(ticket, rule, based_on='COMPLETION')
                    call_kwargs = MockCalc.call_args[1]
                    # 1000 * 1.0 * 0.8 = 800
                    assert call_kwargs['calculated_amount'] == Decimal('800.0')


class TestCalculateWon:
    def test_won_not_won_returns_none(self):
        calc, db = make_calculator()
        ticket = make_ticket(opportunity_id=None, project_id=None)
        rule = make_rule()
        with patch.object(calc, 'check_trigger_condition', return_value=True):
            result = calc.calculate(ticket, rule, based_on='WON')
            assert result is None

    def test_won_opportunity_won(self):
        calc, db = make_calculator()
        ticket = make_ticket(opportunity_id=5, project_id=None)
        rule = make_rule(coefficient=Decimal('2'))

        opp = MagicMock()
        opp.stage = 'WON'
        opp.est_amount = Decimal('100000')

        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = opp
        db.query.return_value = q

        with patch.object(calc, 'check_trigger_condition', return_value=True):
            with patch.object(calc, 'generate_calculation_code', return_value='CALC-WON-001'):
                with patch('app.services.bonus.presale.BonusCalculation') as MockCalc:
                    MockCalc.return_value = MagicMock()
                    result = calc.calculate(ticket, rule, based_on='WON')
                    assert result is not None
                    call_kwargs = MockCalc.call_args[1]
                    # 100000 * (2/100) = 2000
                    assert call_kwargs['calculated_amount'] == Decimal('2000.00')
