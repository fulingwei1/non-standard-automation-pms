# -*- coding: utf-8 -*-
"""Unit tests for app/services/bonus/project.py - batch 41"""
import pytest

pytest.importorskip("app.services.bonus.project")

from unittest.mock import MagicMock, patch
from decimal import Decimal


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def calculator(db):
    with patch("app.services.bonus.project.ProjectEvaluationService"):
        from app.services.bonus.project import ProjectBonusCalculator
        return ProjectBonusCalculator(db)


def test_instantiation(calculator):
    assert calculator is not None


def test_calculate_by_contribution_returns_none_if_condition_not_met(calculator):
    rule = MagicMock()
    rule.trigger_condition = {"stage": "S3"}
    project = MagicMock()
    project.stage = "S1"
    contrib = MagicMock()
    result = calculator.calculate_by_contribution(contrib, project, rule)
    assert result is None


def test_calculate_by_contribution_creates_bonus(calculator, db):
    rule = MagicMock()
    rule.trigger_condition = None
    rule.id = 1
    rule.coefficient = Decimal("5")
    project = MagicMock()
    project.id = 1
    project.contract_amount = Decimal("100000")
    contrib = MagicMock()
    contrib.user_id = 1
    contrib.id = 1
    contrib.hours_percentage = Decimal("50")
    contrib.hours_spent = Decimal("100")

    with patch("app.services.bonus.project.ProjectEvaluationService") as MockEval, \
         patch("app.services.bonus.project.BonusCalculation") as MockCalc:
        eval_svc = MockEval.return_value
        eval_svc.get_difficulty_bonus_coefficient.return_value = Decimal("1.0")
        eval_svc.get_new_tech_bonus_coefficient.return_value = Decimal("1.2")
        MockCalc.return_value = MagicMock()
        result = calculator.calculate_by_contribution(contrib, project, rule)
        assert result is not None


def test_calculate_by_milestone_returns_empty_if_no_members(calculator, db):
    rule = MagicMock()
    rule.trigger_condition = None
    project = MagicMock()
    project.id = 1
    milestone = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    result = calculator.calculate_by_milestone(milestone, project, rule)
    assert result == []


def test_calculate_by_milestone_creates_per_member(calculator, db):
    rule = MagicMock()
    rule.trigger_condition = None
    rule.id = 2
    rule.base_amount = Decimal("1000")
    project = MagicMock()
    project.id = 1
    milestone = MagicMock()
    milestone.milestone_name = "M1"
    milestone.milestone_type = "DELIVERY"
    member = MagicMock()
    member.user_id = 10
    member.role_code = "PM"
    db.query.return_value.filter.return_value.all.return_value = [member]

    with patch("app.services.bonus.project.ProjectEvaluationService") as MockEval, \
         patch("app.services.bonus.project.BonusCalculation") as MockCalc:
        eval_svc = MockEval.return_value
        eval_svc.get_bonus_coefficient.return_value = Decimal("1.0")
        MockCalc.return_value = MagicMock()
        result = calculator.calculate_by_milestone(milestone, project, rule)
        assert len(result) == 1


def test_calculate_by_stage_returns_empty_if_no_members(calculator, db):
    rule = MagicMock()
    rule.trigger_condition = None
    project = MagicMock()
    project.id = 1
    db.query.return_value.filter.return_value.all.return_value = []
    result = calculator.calculate_by_stage(project, "S1", "S2", rule)
    assert result == []


def test_calculate_by_stage_creates_calculations(calculator, db):
    rule = MagicMock()
    rule.trigger_condition = None
    rule.id = 3
    rule.base_amount = Decimal("500")
    project = MagicMock()
    project.id = 1
    project.contract_amount = Decimal("50000")
    member = MagicMock()
    member.user_id = 5
    member.role_code = "ME"
    db.query.return_value.filter.return_value.all.return_value = [member]

    with patch("app.services.bonus.project.ProjectEvaluationService") as MockEval, \
         patch("app.services.bonus.project.BonusCalculation") as MockCalc:
        eval_svc = MockEval.return_value
        eval_svc.get_bonus_coefficient.return_value = Decimal("1.1")
        MockCalc.return_value = MagicMock()
        result = calculator.calculate_by_stage(project, "S1", "S2", rule)
        assert len(result) == 1
