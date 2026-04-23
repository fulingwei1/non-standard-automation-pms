# -*- coding: utf-8 -*-
"""方案工程师奖金服务深度测试"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.services.bonus.solution_engineer_bonus_service import SolutionEngineerBonusService


class FakeQuery:
    def __init__(self, *, first_value=None, all_value=None):
        self.first_value = first_value
        self.all_value = all_value if all_value is not None else []

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.first_value

    def all(self):
        return self.all_value


class TestSolutionEngineerBonusServiceDeep:
    def test_calculate_solution_bonus_period_not_found(self):
        db = Mock()
        db.query.return_value = FakeQuery(first_value=None)
        service = SolutionEngineerBonusService(db)

        with pytest.raises(ValueError, match="考核周期不存在"):
            service.calculate_solution_bonus(engineer_id=1, period_id=99)

    def test_calculate_solution_bonus_returns_zero_when_no_solutions(self):
        period = SimpleNamespace(id=1, period_name="2026Q1", start_date=date(2026, 1, 1), end_date=date(2026, 3, 31))
        db = Mock()
        db.query.side_effect = [
            FakeQuery(first_value=period),
            FakeQuery(all_value=[]),
        ]
        service = SolutionEngineerBonusService(db)

        result = service.calculate_solution_bonus(engineer_id=7, period_id=1)

        assert result["engineer_id"] == 7
        assert result["total_solutions"] == 0
        assert result["total_bonus"] == 0.0
        assert result["details"] == []

    def test_calculate_solution_bonus_covers_won_high_quality_and_success_rate(self):
        period = SimpleNamespace(id=1, period_name="2026Q1", start_date=date(2026, 1, 1), end_date=date(2026, 3, 31))
        won_solution = SimpleNamespace(
            id=11,
            solution_no="S001",
            name="中标方案",
            status="APPROVED",
            opportunity_id=101,
            ticket_id=None,
        )
        high_quality_unwon = SimpleNamespace(
            id=12,
            solution_no="S002",
            name="高质量未中标方案",
            status="SUBMITTED",
            opportunity_id=None,
            ticket_id=202,
        )
        signed_contract = SimpleNamespace(contract_amount=Decimal("100000"))
        high_quality_ticket = SimpleNamespace(satisfaction_score=4.8)

        db = Mock()
        db.query.side_effect = [
            FakeQuery(first_value=period),
            FakeQuery(all_value=[won_solution, high_quality_unwon]),
            FakeQuery(first_value=signed_contract),
            FakeQuery(first_value=high_quality_ticket),
        ]
        service = SolutionEngineerBonusService(db)

        result = service.calculate_solution_bonus(engineer_id=3, period_id=1)

        assert result["total_solutions"] == 2
        assert result["won_solutions"] == 1
        assert result["win_rate"] == 50.0
        assert result["completion_bonus"] == 1000.0
        assert result["won_bonus"] == 100.0
        assert result["high_quality_compensation"] == 300.0
        assert result["success_rate_bonus"] == 2000.0
        assert result["total_bonus"] == 3400.0
        assert result["details"][0]["is_won"] is True
        assert result["details"][1]["is_high_quality"] is True

    def test_get_solution_score_details_period_not_found(self):
        db = Mock()
        db.query.return_value = FakeQuery(first_value=None)
        service = SolutionEngineerBonusService(db)

        with pytest.raises(ValueError, match="考核周期不存在"):
            service.get_solution_score_details(engineer_id=1, period_id=99)

    def test_get_solution_score_details_returns_dimension_and_statistics(self):
        period = SimpleNamespace(id=1, start_date=date(2026, 1, 1), end_date=date(2026, 3, 31))
        approved_won_solution = SimpleNamespace(review_status="APPROVED", opportunity_id=101, ticket_id=201)
        normal_solution = SimpleNamespace(review_status="DRAFT", opportunity_id=None, ticket_id=None)
        score = SimpleNamespace(
            technical_score=Decimal("90"),
            execution_score=Decimal("88"),
            cost_quality_score=Decimal("86"),
            knowledge_score=Decimal("84"),
            collaboration_score=Decimal("82"),
            solution_success_score=Decimal("80"),
        )
        contract = SimpleNamespace(contract_amount=Decimal("50000"))
        ticket = SimpleNamespace(satisfaction_score=4.9)

        db = Mock()
        db.query.side_effect = [
            FakeQuery(first_value=period),
            FakeQuery(all_value=[approved_won_solution, normal_solution]),
            FakeQuery(first_value=contract),
            FakeQuery(first_value=ticket),
        ]
        service = SolutionEngineerBonusService(db)

        fake_eps_instance = Mock()
        fake_eps_instance._calculate_solution_score.return_value = score

        with patch(
            "app.services.engineer_performance.engineer_performance_service.EngineerPerformanceService",
            return_value=fake_eps_instance,
        ):
            result = service.get_solution_score_details(engineer_id=5, period_id=1)

        assert result["dimension_scores"]["technical_score"] == 90.0
        assert result["dimension_scores"]["solution_success_score"] == 80.0
        assert result["solution_statistics"]["total_solutions"] == 2
        assert result["solution_statistics"]["won_solutions"] == 1
        assert result["solution_statistics"]["approved_solutions"] == 1
        assert result["solution_statistics"]["high_quality_solutions"] == 1
        assert result["solution_statistics"]["win_rate"] == 50.0
        assert result["solution_statistics"]["approval_rate"] == 50.0
