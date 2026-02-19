# -*- coding: utf-8 -*-
"""Unit tests for app/services/bonus/sales.py - batch 41"""
import pytest

pytest.importorskip("app.services.bonus.sales")

from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def calculator(db):
    from app.services.bonus.sales import SalesBonusCalculator
    return SalesBonusCalculator(db)


def test_instantiation(calculator):
    assert calculator is not None


def test_calculate_returns_none_if_no_owner(calculator):
    contract = MagicMock()
    contract.owner_id = None
    rule = MagicMock()
    rule.trigger_condition = None
    result = calculator.calculate(contract, rule)
    assert result is None


def test_calculate_by_contract(calculator):
    contract = MagicMock()
    contract.owner_id = 1
    contract.project_id = 2
    contract.id = 10
    contract.contract_code = "C001"
    contract.contract_amount = Decimal("100000")
    rule = MagicMock()
    rule.trigger_condition = None
    rule.id = 1
    rule.coefficient = Decimal("3")

    with patch("app.services.bonus.sales.BonusCalculation") as MockCalc:
        MockCalc.return_value = MagicMock()
        result = calculator.calculate(contract, rule, based_on="CONTRACT")
        assert result is not None
        kwargs = MockCalc.call_args[1]
        # 100000 * 3 / 100 = 3000
        assert kwargs["calculated_amount"] == Decimal("3000")


def test_calculate_by_payment_no_paid_invoices(calculator, db):
    contract = MagicMock()
    contract.owner_id = 1
    contract.id = 5
    contract.contract_amount = Decimal("50000")
    rule = MagicMock()
    rule.trigger_condition = None
    rule.coefficient = Decimal("2")
    db.query.return_value.filter.return_value.all.return_value = []
    result = calculator.calculate(contract, rule, based_on="PAYMENT")
    assert result is None


def test_calculate_by_payment_with_paid_invoices(calculator, db):
    contract = MagicMock()
    contract.owner_id = 1
    contract.project_id = 3
    contract.id = 6
    contract.contract_code = "C002"
    contract.contract_amount = Decimal("80000")
    rule = MagicMock()
    rule.trigger_condition = None
    rule.id = 2
    rule.coefficient = Decimal("2")
    inv = MagicMock()
    inv.paid_amount = Decimal("40000")
    inv.total_amount = Decimal("40000")
    inv.id = 1
    db.query.return_value.filter.return_value.all.return_value = [inv]

    with patch("app.services.bonus.sales.BonusCalculation") as MockCalc:
        MockCalc.return_value = MagicMock()
        result = calculator.calculate(contract, rule, based_on="PAYMENT")
        assert result is not None


def test_calculate_director_bonus_no_contracts(calculator, db):
    rule = MagicMock()
    rule.trigger_condition = None
    # Mock the entire db.query chain to avoid SQLAlchemy attribute access
    db.query.return_value.filter.return_value.all.return_value = []
    with patch("app.services.bonus.sales.Contract") as MockContract:
        # Make filter comparisons work by returning mock expressions
        mock_col = MagicMock()
        mock_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_col.__le__ = MagicMock(return_value=MagicMock())
        MockContract.signed_date = mock_col
        MockContract.status = MagicMock()
        result = calculator.calculate_director_bonus(1, date(2025, 1, 1), date(2025, 12, 31), rule)
    assert result is None


def test_calculate_director_bonus_with_contracts(calculator, db):
    rule = MagicMock()
    rule.trigger_condition = None
    rule.id = 3
    rule.coefficient = Decimal("1")
    contract = MagicMock()
    contract.contract_amount = Decimal("200000")
    contract.owner_id = 5
    contract.id = 1
    db.query.return_value.filter.return_value.all.return_value = [contract]
    with patch("app.services.bonus.sales.Contract") as MockContract:
        mock_col = MagicMock()
        mock_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_col.__le__ = MagicMock(return_value=MagicMock())
        MockContract.signed_date = mock_col
        MockContract.status = MagicMock()
        with patch("app.services.bonus.sales.BonusCalculation") as MockCalc:
            MockCalc.return_value = MagicMock()
            result = calculator.calculate_director_bonus(
                1, date(2025, 1, 1), date(2025, 12, 31), rule
            )
    assert result is not None
