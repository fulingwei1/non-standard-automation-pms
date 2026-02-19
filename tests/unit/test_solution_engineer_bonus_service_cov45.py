# -*- coding: utf-8 -*-
"""
第四十五批覆盖：solution_engineer_bonus_service.py
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock

pytest.importorskip("app.services.solution_engineer_bonus_service")

from app.services.solution_engineer_bonus_service import SolutionEngineerBonusService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return SolutionEngineerBonusService(mock_db)


def _make_period(period_id=1, name="2024Q1"):
    period = MagicMock()
    period.id = period_id
    period.period_name = name
    period.start_date = "2024-01-01"
    period.end_date = "2024-03-31"
    return period


def _make_solution(sol_id=1, status="APPROVED", opportunity_id=None, ticket_id=None):
    s = MagicMock()
    s.id = sol_id
    s.status = status
    s.opportunity_id = opportunity_id
    s.ticket_id = ticket_id
    s.solution_no = f"SOL-{sol_id}"
    s.name = f"方案{sol_id}"
    return s


class TestSolutionEngineerBonusService:
    def test_period_not_found_raises(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="考核周期不存在"):
            service.calculate_solution_bonus(engineer_id=1, period_id=999)

    def test_no_solutions_returns_zero(self, service, mock_db):
        period = _make_period()
        mock_db.query.return_value.filter.return_value.first.return_value = period
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = service.calculate_solution_bonus(engineer_id=1, period_id=1)
        assert result["total_solutions"] == 0
        assert result["total_bonus"] == 0.0
        assert result["completion_bonus"] == 0.0

    def test_completion_bonus_for_approved_solution(self, service, mock_db):
        period = _make_period()
        solution = _make_solution(status="APPROVED")

        # period query
        mock_db.query.return_value.filter.return_value.first.return_value = period
        mock_db.query.return_value.filter.return_value.all.return_value = [solution]
        # no contract
        mock_db.query.return_value.filter.return_value.first.side_effect = [period, None]

        result = service.calculate_solution_bonus(engineer_id=1, period_id=1)
        assert result["completion_bonus"] == 500.0

    def test_won_bonus_with_contract(self, service, mock_db):
        period = _make_period()
        solution = _make_solution(status="APPROVED", opportunity_id=10)
        contract = MagicMock()
        contract.contract_amount = Decimal("1000000")
        contract.status = "SIGNED"

        call_results = [period, contract]
        mock_db.query.return_value.filter.return_value.first.side_effect = call_results
        mock_db.query.return_value.filter.return_value.all.return_value = [solution]

        result = service.calculate_solution_bonus(engineer_id=1, period_id=1)
        # won_bonus = 1,000,000 * 0.001 = 1000
        assert result["won_bonus"] == pytest.approx(1000.0)

    def test_success_rate_bonus_triggers_at_40_percent(self, service, mock_db):
        period = _make_period()
        # 2 won solutions, 3 total -> 66.7% win rate >= 40%
        solutions = [_make_solution(i, "APPROVED", opportunity_id=i) for i in range(1, 4)]
        contracts = [MagicMock(contract_amount=Decimal("100000"), status="SIGNED")] * 2 + [None]

        mock_db.query.return_value.filter.return_value.first.side_effect = [period] + contracts
        mock_db.query.return_value.filter.return_value.all.return_value = solutions

        result = service.calculate_solution_bonus(engineer_id=1, period_id=1)
        assert result["success_rate_bonus"] == 2000.0

    def test_win_rate_below_40_no_success_bonus(self, service, mock_db):
        period = _make_period()
        # 1 won, 5 total -> 20% win rate < 40%
        solutions = [_make_solution(i, "APPROVED", opportunity_id=None) for i in range(1, 6)]
        solutions[0].opportunity_id = 99

        contract = MagicMock(contract_amount=Decimal("100000"), status="SIGNED")
        mock_db.query.return_value.filter.return_value.first.side_effect = [period, contract] + [None] * 10
        mock_db.query.return_value.filter.return_value.all.return_value = solutions

        result = service.calculate_solution_bonus(engineer_id=1, period_id=1)
        assert result["success_rate_bonus"] == 0.0

    def test_result_contains_details(self, service, mock_db):
        period = _make_period()
        mock_db.query.return_value.filter.return_value.first.return_value = period
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = service.calculate_solution_bonus(engineer_id=1, period_id=1)
        assert "details" in result
        assert isinstance(result["details"], list)
