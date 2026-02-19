# -*- coding: utf-8 -*-
"""Unit tests for app/services/bonus/calculator.py - batch 41"""
import pytest

pytest.importorskip("app.services.bonus.calculator")

from unittest.mock import MagicMock, patch


@pytest.fixture
def db():
    return MagicMock()


def _make_calculator(db):
    patches = [
        patch("app.services.bonus.calculator.PerformanceBonusCalculator"),
        patch("app.services.bonus.calculator.ProjectBonusCalculator"),
        patch("app.services.bonus.calculator.SalesBonusCalculator"),
        patch("app.services.bonus.calculator.TeamBonusCalculator"),
        patch("app.services.bonus.calculator.PresaleBonusCalculator"),
        patch("app.services.bonus.calculator.AcceptanceBonusTrigger"),
    ]
    mocks = [p.start() for p in patches]
    from app.services.bonus.calculator import BonusCalculator
    calc = BonusCalculator(db)
    for p in patches:
        p.stop()
    return calc


def test_bonus_calculator_instantiation(db):
    calc = _make_calculator(db)
    assert calc is not None


def test_calculate_performance_bonus_delegates(db):
    calc = _make_calculator(db)
    perf = MagicMock()
    rule = MagicMock()
    calc.performance_calculator = MagicMock()
    calc.performance_calculator.calculate.return_value = MagicMock()
    result = calc.calculate_performance_bonus(perf, rule)
    calc.performance_calculator.calculate.assert_called_once_with(perf, rule)


def test_calculate_project_bonus_delegates(db):
    calc = _make_calculator(db)
    contribution = MagicMock()
    project = MagicMock()
    rule = MagicMock()
    calc.project_calculator = MagicMock()
    calc.project_calculator.calculate_by_contribution.return_value = MagicMock()
    calc.calculate_project_bonus(contribution, project, rule)
    calc.project_calculator.calculate_by_contribution.assert_called_once_with(contribution, project, rule)


def test_calculate_milestone_bonus_delegates(db):
    calc = _make_calculator(db)
    milestone = MagicMock()
    project = MagicMock()
    rule = MagicMock()
    calc.project_calculator = MagicMock()
    calc.project_calculator.calculate_by_milestone.return_value = []
    result = calc.calculate_milestone_bonus(milestone, project, rule)
    calc.project_calculator.calculate_by_milestone.assert_called_once()


def test_calculate_sales_bonus_delegates(db):
    calc = _make_calculator(db)
    contract = MagicMock()
    rule = MagicMock()
    calc.sales_calculator = MagicMock()
    calc.sales_calculator.calculate.return_value = MagicMock()
    calc.calculate_sales_bonus(contract, rule)
    calc.sales_calculator.calculate.assert_called_once()


def test_calculate_team_bonus_delegates(db):
    calc = _make_calculator(db)
    project = MagicMock()
    rule = MagicMock()
    calc.team_calculator = MagicMock()
    calc.team_calculator.calculate.return_value = MagicMock()
    result = calc.calculate_team_bonus(project, rule)
    calc.team_calculator.calculate.assert_called_once_with(project, rule, None)


def test_trigger_acceptance_bonus_delegates(db):
    calc = _make_calculator(db)
    project = MagicMock()
    acceptance = MagicMock()
    calc.acceptance_trigger = MagicMock()
    calc.acceptance_trigger.trigger_calculation.return_value = []
    result = calc.trigger_acceptance_bonus_calculation(project, acceptance)
    calc.acceptance_trigger.trigger_calculation.assert_called_once_with(project, acceptance)
