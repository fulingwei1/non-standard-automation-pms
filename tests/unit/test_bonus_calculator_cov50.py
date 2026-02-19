# -*- coding: utf-8 -*-
"""
Unit tests for app/services/bonus/calculator.py
批次: cov50
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

try:
    from app.services.bonus.calculator import BonusCalculator
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_calculator():
    db = MagicMock()
    with patch("app.services.bonus.calculator.PerformanceBonusCalculator"), \
         patch("app.services.bonus.calculator.ProjectBonusCalculator"), \
         patch("app.services.bonus.calculator.SalesBonusCalculator"), \
         patch("app.services.bonus.calculator.TeamBonusCalculator"), \
         patch("app.services.bonus.calculator.PresaleBonusCalculator"), \
         patch("app.services.bonus.calculator.AcceptanceBonusTrigger"):
        return BonusCalculator(db=db)


def test_bonus_calculator_instantiation():
    """BonusCalculator 应能正常实例化"""
    calc = _make_calculator()
    assert calc is not None
    assert hasattr(calc, 'performance_calculator')
    assert hasattr(calc, 'project_calculator')
    assert hasattr(calc, 'sales_calculator')
    assert hasattr(calc, 'team_calculator')


def test_calculate_performance_bonus_delegates():
    """calculate_performance_bonus 应委托给 performance_calculator"""
    calc = _make_calculator()
    mock_result = MagicMock()
    calc.performance_calculator.calculate.return_value = mock_result

    pr = MagicMock()
    rule = MagicMock()
    result = calc.calculate_performance_bonus(pr, rule)

    calc.performance_calculator.calculate.assert_called_once_with(pr, rule)
    assert result is mock_result


def test_calculate_project_bonus_delegates():
    """calculate_project_bonus 应委托给 project_calculator"""
    calc = _make_calculator()
    mock_result = MagicMock()
    calc.project_calculator.calculate_by_contribution.return_value = mock_result

    contrib = MagicMock()
    project = MagicMock()
    rule = MagicMock()
    result = calc.calculate_project_bonus(contrib, project, rule)

    calc.project_calculator.calculate_by_contribution.assert_called_once_with(contrib, project, rule)
    assert result is mock_result


def test_calculate_milestone_bonus_delegates():
    """calculate_milestone_bonus 应委托给 project_calculator"""
    calc = _make_calculator()
    mock_result = [MagicMock()]
    calc.project_calculator.calculate_by_milestone.return_value = mock_result

    milestone = MagicMock()
    project = MagicMock()
    rule = MagicMock()
    result = calc.calculate_milestone_bonus(milestone, project, rule)

    calc.project_calculator.calculate_by_milestone.assert_called_once()
    assert result is mock_result


def test_calculate_stage_bonus_delegates():
    """calculate_stage_bonus 应委托给 project_calculator"""
    calc = _make_calculator()
    mock_result = [MagicMock()]
    calc.project_calculator.calculate_by_stage.return_value = mock_result

    project = MagicMock()
    rule = MagicMock()
    result = calc.calculate_stage_bonus(project, "TESTING", "ACCEPTANCE", rule)

    calc.project_calculator.calculate_by_stage.assert_called_once()
    assert result is mock_result


def test_calculate_sales_bonus_delegates():
    """calculate_sales_bonus 应委托给 sales_calculator"""
    calc = _make_calculator()
    mock_result = MagicMock()
    calc.sales_calculator.calculate.return_value = mock_result

    contract = MagicMock()
    rule = MagicMock()
    result = calc.calculate_sales_bonus(contract, rule)

    calc.sales_calculator.calculate.assert_called_once()
    assert result is mock_result


def test_calculate_team_bonus_delegates():
    """calculate_team_bonus 应委托给 team_calculator"""
    calc = _make_calculator()
    mock_result = MagicMock()
    calc.team_calculator.calculate.return_value = mock_result

    project = MagicMock()
    rule = MagicMock()
    result = calc.calculate_team_bonus(project, rule)

    calc.team_calculator.calculate.assert_called_once()
    assert result is mock_result


def test_trigger_acceptance_bonus_calculation_delegates():
    """trigger_acceptance_bonus_calculation 应委托给 acceptance_trigger"""
    calc = _make_calculator()
    mock_result = [MagicMock()]
    calc.acceptance_trigger.trigger_calculation.return_value = mock_result

    project = MagicMock()
    acceptance = MagicMock()
    result = calc.trigger_acceptance_bonus_calculation(project, acceptance)

    calc.acceptance_trigger.trigger_calculation.assert_called_once_with(project, acceptance)
    assert result is mock_result
