# -*- coding: utf-8 -*-
"""第二十三批：cost_allocation_service 单元测试"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.cost_allocation_service")

from app.services.cost_allocation_service import (
    query_allocatable_costs,
    get_target_project_ids,
    calculate_allocation_rates_by_hours,
    calculate_allocation_rates_by_headcount,
    calculate_allocation_rates,
    create_allocated_cost,
)


def _mock_rule(project_ids=None, cost_type_ids=None, allocation_basis="EQUAL"):
    r = MagicMock()
    r.project_ids = project_ids or []
    r.cost_type_ids = cost_type_ids or []
    r.allocation_basis = allocation_basis
    return r


def _mock_cost(cost_no="C001", cost_amount=Decimal("1000"), cost_type_id=1,
               status="APPROVED", is_allocated=False):
    c = MagicMock()
    c.cost_no = cost_no
    c.cost_amount = cost_amount
    c.cost_type_id = cost_type_id
    c.status = status
    c.is_allocated = is_allocated
    c.cost_date = None
    c.cost_description = "测试费用"
    c.deductible_amount = None
    return c


def _mock_project(pid=1, total_hours=100, participant_count=5, total_cost=Decimal("5000")):
    p = MagicMock()
    p.id = pid
    p.total_hours = total_hours
    p.participant_count = participant_count
    p.total_cost = total_cost
    return p


class TestQueryAllocatableCosts:
    def test_filters_approved_unallocated(self):
        db = MagicMock()
        rule = _mock_rule()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q
        result = query_allocatable_costs(db, rule, None)
        assert result == []

    def test_filters_by_cost_ids(self):
        db = MagicMock()
        rule = _mock_rule()
        cost = _mock_cost()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [cost]
        db.query.return_value = q
        result = query_allocatable_costs(db, rule, [1])
        assert len(result) == 1


class TestGetTargetProjectIds:
    def test_uses_rule_project_ids(self):
        db = MagicMock()
        rule = _mock_rule(project_ids=[1, 2, 3])
        result = get_target_project_ids(db, rule)
        assert result == [1, 2, 3]

    def test_queries_approved_projects_when_empty(self):
        db = MagicMock()
        rule = _mock_rule(project_ids=[])
        proj1 = _mock_project(1)
        proj2 = _mock_project(2)
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [proj1, proj2]
        db.query.return_value = q
        result = get_target_project_ids(db, rule)
        assert 1 in result and 2 in result


class TestCalculateAllocationRatesByHours:
    def test_proportional_rates(self):
        db = MagicMock()
        p1 = _mock_project(1, total_hours=200)
        p2 = _mock_project(2, total_hours=200)

        def query_side(model):
            q = MagicMock()
            q.filter.return_value.first.side_effect = [p1, p2]
            return q

        db.query.side_effect = query_side
        # Reset side effects
        call_count = [0]
        def filter_side(*a, **kw):
            q2 = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                q2.first.return_value = p1
            else:
                q2.first.return_value = p2
            return q2

        q = MagicMock()
        q.filter.side_effect = filter_side
        db.query.return_value = q
        result = calculate_allocation_rates_by_hours(db, [1, 2])
        total = sum(result.values())
        assert abs(total - 100.0) < 0.01

    def test_equal_when_no_hours(self):
        db = MagicMock()
        p1 = _mock_project(1, total_hours=0)
        q = MagicMock()
        q.filter.return_value.first.return_value = p1
        db.query.return_value = q
        result = calculate_allocation_rates_by_hours(db, [1, 2])
        assert result[1] == pytest.approx(50.0)
        assert result[2] == pytest.approx(50.0)


class TestCalculateAllocationRatesByHeadcount:
    def test_equal_when_no_participants(self):
        db = MagicMock()
        p = _mock_project(1, participant_count=0)
        q = MagicMock()
        q.filter.return_value.first.return_value = p
        db.query.return_value = q
        result = calculate_allocation_rates_by_headcount(db, [1, 2])
        assert result[1] == pytest.approx(50.0)


class TestCalculateAllocationRates:
    def test_hours_basis_delegates(self):
        db = MagicMock()
        rule = _mock_rule(allocation_basis="HOURS")
        with patch("app.services.cost_allocation_service.calculate_allocation_rates_by_hours", return_value={1: 100.0}) as mock_fn:
            result = calculate_allocation_rates(db, rule, [1])
        mock_fn.assert_called_once()

    def test_headcount_basis_delegates(self):
        db = MagicMock()
        rule = _mock_rule(allocation_basis="HEADCOUNT")
        with patch("app.services.cost_allocation_service.calculate_allocation_rates_by_headcount", return_value={1: 100.0}) as mock_fn:
            result = calculate_allocation_rates(db, rule, [1])
        mock_fn.assert_called_once()

    def test_default_equal_split(self):
        db = MagicMock()
        rule = _mock_rule(allocation_basis="EQUAL")
        result = calculate_allocation_rates(db, rule, [1, 2])
        assert result[1] == pytest.approx(50.0)
        assert result[2] == pytest.approx(50.0)


class TestCreateAllocatedCost:
    def test_creates_cost_with_correct_amount(self):
        db = MagicMock()
        cost = _mock_cost(cost_amount=Decimal("1000"))
        proj = _mock_project(total_cost=Decimal("0"))
        q = MagicMock()
        q.filter.return_value.first.return_value = proj
        db.query.return_value = q
        generate_cost_no = MagicMock(return_value="C-NEW-001")
        result = create_allocated_cost(db, cost, 1, 50.0, 10, generate_cost_no)
        assert result.cost_amount == Decimal("500")
        db.add.assert_called_once_with(result)
