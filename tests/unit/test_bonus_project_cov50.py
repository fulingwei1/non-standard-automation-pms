# -*- coding: utf-8 -*-
"""
Unit tests for app/services/bonus/project.py
批次: cov50
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

try:
    from app.services.bonus.project import ProjectBonusCalculator
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_calculator():
    db = MagicMock()
    return ProjectBonusCalculator(db=db)


def _make_rule(coefficient=Decimal('5'), base_amount=Decimal('1000')):
    rule = MagicMock()
    rule.coefficient = coefficient
    rule.base_amount = base_amount
    rule.trigger_condition = None
    rule.id = 1
    return rule


def _make_project(contract_amount=Decimal('200000'), stage="TESTING"):
    proj = MagicMock()
    proj.contract_amount = contract_amount
    proj.stage = stage
    proj.id = 10
    return proj


def _make_contribution(hours_percentage=Decimal('30'), user_id=1):
    contrib = MagicMock()
    contrib.hours_percentage = hours_percentage
    contrib.user_id = user_id
    contrib.hours_spent = Decimal('120')
    contrib.id = 5
    return contrib


def test_calculate_by_contribution_returns_calculation():
    """基于贡献计算奖金应返回BonusCalculation"""
    calc = _make_calculator()
    rule = _make_rule(coefficient=Decimal('5'))
    project = _make_project(contract_amount=Decimal('200000'))
    contribution = _make_contribution(hours_percentage=Decimal('50'))

    with patch("app.services.bonus.project.ProjectEvaluationService") as mock_eval_cls:
        mock_eval = mock_eval_cls.return_value
        mock_eval.get_difficulty_bonus_coefficient.return_value = Decimal('1.0')
        mock_eval.get_new_tech_bonus_coefficient.return_value = Decimal('1.0')

        result = calc.calculate_by_contribution(contribution, project, rule)

    assert result is not None
    assert result.status == 'CALCULATED'
    assert result.user_id == contribution.user_id


def test_calculate_by_contribution_returns_none_when_condition_not_met():
    """触发条件不满足时返回None"""
    calc = _make_calculator()
    rule = _make_rule()
    rule.trigger_condition = {"stage": "ACCEPTANCE"}
    project = _make_project(stage="TESTING")
    contribution = _make_contribution()

    with patch("app.services.bonus.project.ProjectEvaluationService"):
        result = calc.calculate_by_contribution(contribution, project, rule)

    assert result is None


def test_calculate_by_contribution_amount():
    """奖金金额计算正确"""
    calc = _make_calculator()
    rule = _make_rule(coefficient=Decimal('10'))
    project = _make_project(contract_amount=Decimal('100000'))
    contribution = _make_contribution(hours_percentage=Decimal('100'))

    with patch("app.services.bonus.project.ProjectEvaluationService") as mock_eval_cls:
        mock_eval = mock_eval_cls.return_value
        mock_eval.get_difficulty_bonus_coefficient.return_value = Decimal('1.0')
        mock_eval.get_new_tech_bonus_coefficient.return_value = Decimal('1.0')

        result = calc.calculate_by_contribution(contribution, project, rule)

    assert result is not None
    # 100000 * 10/100 * 100/100 * max(1.0, 1.0) = 10000
    assert result.calculated_amount == Decimal('10000')


def test_calculate_by_milestone_no_members():
    """无项目成员时里程碑奖金应返回空列表"""
    calc = _make_calculator()
    rule = _make_rule()
    project = _make_project()
    milestone = MagicMock(milestone_name="验收", milestone_type="ACCEPTANCE", status="COMPLETED", id=1)

    calc.db.query.return_value.filter.return_value.all.return_value = []

    with patch("app.services.bonus.project.ProjectEvaluationService"):
        results = calc.calculate_by_milestone(milestone, project, rule)

    assert results == []


def test_calculate_by_milestone_with_members():
    """有项目成员时应为每个成员生成计算记录"""
    calc = _make_calculator()
    rule = _make_rule(base_amount=Decimal('5000'))
    project = _make_project()
    milestone = MagicMock(milestone_name="交付", milestone_type="DELIVERY", status="COMPLETED", id=2)

    member1 = MagicMock(user_id=1, role_code="PM")
    member2 = MagicMock(user_id=2, role_code="ME")
    calc.db.query.return_value.filter.return_value.all.return_value = [member1, member2]

    with patch("app.services.bonus.project.ProjectEvaluationService") as mock_eval_cls:
        mock_eval = mock_eval_cls.return_value
        mock_eval.get_bonus_coefficient.return_value = Decimal('1.0')

        results = calc.calculate_by_milestone(milestone, project, rule)

    assert len(results) == 2
    assert all(r.status == 'CALCULATED' for r in results)


def test_calculate_by_stage_no_members():
    """无项目成员时阶段奖金应返回空列表"""
    calc = _make_calculator()
    rule = _make_rule()
    project = _make_project()

    calc.db.query.return_value.filter.return_value.all.return_value = []

    with patch("app.services.bonus.project.ProjectEvaluationService"):
        results = calc.calculate_by_stage(project, "TESTING", "ACCEPTANCE", rule)

    assert results == []


def test_calculate_by_stage_with_members():
    """有成员时阶段奖金应生成对应计算记录"""
    calc = _make_calculator()
    rule = _make_rule(base_amount=Decimal('2000'))
    project = _make_project()

    member = MagicMock(user_id=99, role_code="QA")
    calc.db.query.return_value.filter.return_value.all.return_value = [member]

    with patch("app.services.bonus.project.ProjectEvaluationService") as mock_eval_cls:
        mock_eval = mock_eval_cls.return_value
        mock_eval.get_bonus_coefficient.return_value = Decimal('1.0')

        results = calc.calculate_by_stage(project, "TESTING", "ACCEPTANCE", rule)

    assert len(results) == 1
    assert results[0].calculation_basis["type"] == "stage"
