# -*- coding: utf-8 -*-
"""cost_allocation_service 深度测试"""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.cost.cost_allocation_service import (
    calculate_allocation_rates,
    calculate_allocation_rates_by_headcount,
    calculate_allocation_rates_by_hours,
    create_allocated_cost,
    get_target_project_ids,
    query_allocatable_costs,
)


class FakeQuery:
    def __init__(self, first_value=None, all_value=None):
        self._first_value = first_value
        self._all_value = all_value or []

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self._all_value

    def first(self):
        return self._first_value


class TestCostAllocationServiceDeep:
    def test_query_allocatable_costs_with_explicit_cost_ids(self):
        db = Mock()
        query = FakeQuery(all_value=["c1", "c2"])
        db.query.return_value = query
        rule = SimpleNamespace(cost_type_ids=[1, 2])

        result = query_allocatable_costs(db, rule, [10, 11])

        assert result == ["c1", "c2"]

    def test_get_target_project_ids_uses_rule_ids_first(self):
        db = Mock()
        rule = SimpleNamespace(project_ids=[1, 2, 3])

        result = get_target_project_ids(db, rule)

        assert result == [1, 2, 3]
        db.query.assert_not_called()

    def test_get_target_project_ids_fallbacks_to_active_projects(self):
        db = Mock()
        db.query.return_value = FakeQuery(
            all_value=[SimpleNamespace(id=8), SimpleNamespace(id=9)]
        )
        rule = SimpleNamespace(project_ids=[])

        result = get_target_project_ids(db, rule)

        assert result == [8, 9]

    def test_calculate_allocation_rates_by_hours(self):
        db = Mock()
        db.query.side_effect = [
            FakeQuery(first_value=SimpleNamespace(total_hours=10)),
            FakeQuery(first_value=SimpleNamespace(total_hours=30)),
        ]

        result = calculate_allocation_rates_by_hours(db, [1, 2])

        assert result == {1: 25.0, 2: 75.0}

    def test_calculate_allocation_rates_by_hours_fallback_average(self):
        db = Mock()
        db.query.side_effect = [
            FakeQuery(first_value=SimpleNamespace(total_hours=0)),
            FakeQuery(first_value=None),
        ]

        result = calculate_allocation_rates_by_hours(db, [1, 2])

        assert result == {1: 50.0, 2: 50.0}

    def test_calculate_allocation_rates_by_headcount(self):
        db = Mock()
        db.query.side_effect = [
            FakeQuery(first_value=SimpleNamespace(participant_count=2)),
            FakeQuery(first_value=SimpleNamespace(participant_count=6)),
        ]

        result = calculate_allocation_rates_by_headcount(db, [1, 2])

        assert result == {1: 25.0, 2: 75.0}

    def test_calculate_allocation_rates_dispatch(self):
        db = Mock()
        with patch(
            "app.services.cost.cost_allocation_service.calculate_allocation_rates_by_hours",
            return_value={1: 100.0},
        ) as mock_hours, patch(
            "app.services.cost.cost_allocation_service.calculate_allocation_rates_by_headcount",
            return_value={2: 100.0},
        ) as mock_headcount:
            assert calculate_allocation_rates(db, SimpleNamespace(allocation_basis="HOURS"), [1]) == {1: 100.0}
            assert calculate_allocation_rates(db, SimpleNamespace(allocation_basis="HEADCOUNT"), [2]) == {2: 100.0}
            assert calculate_allocation_rates(db, SimpleNamespace(allocation_basis="REVENUE"), [1, 2]) == {1: 50.0, 2: 50.0}
            assert calculate_allocation_rates(db, SimpleNamespace(allocation_basis="OTHER"), [1, 2]) == {1: 50.0, 2: 50.0}
            mock_hours.assert_called_once()
            mock_headcount.assert_called_once()

    def test_create_allocated_cost_updates_project_and_deductible_amount(self):
        db = Mock()
        project = SimpleNamespace(id=9, total_cost=Decimal("200"))
        db.query.return_value = FakeQuery(first_value=project)
        cost = SimpleNamespace(
            id=5,
            cost_no="C-001",
            cost_type_id=7,
            cost_date="2026-04-12",
            cost_amount=Decimal("1000"),
            cost_description="服务器费用",
            deductible_amount=Decimal("200"),
        )

        with patch(
            "app.services.cost.cost_allocation_service.RdCost",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ):
            allocated = create_allocated_cost(db, cost, 9, 25.0, 3, lambda _db: "ALLOC-001")

        assert allocated.cost_no == "ALLOC-001"
        assert allocated.cost_amount == Decimal("250")
        assert allocated.deductible_amount == Decimal("50")
        assert allocated.source_type == "ALLOCATED"
        assert allocated.remark == "由规则3自动分摊"
        assert project.total_cost == Decimal("450")
        db.add.assert_called_once()

    def test_create_allocated_cost_without_deductible_amount(self):
        db = Mock()
        db.query.return_value = FakeQuery(first_value=None)
        cost = SimpleNamespace(
            id=6,
            cost_no="C-002",
            cost_type_id=8,
            cost_date="2026-04-12",
            cost_amount=Decimal("0"),
            cost_description=None,
            deductible_amount=None,
        )

        with patch(
            "app.services.cost.cost_allocation_service.RdCost",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ):
            allocated = create_allocated_cost(db, cost, 10, 50.0, 4, lambda _db: "ALLOC-002")

        assert allocated.cost_description == "（分摊自费用C-002）"
        assert allocated.deductible_amount is None
        assert allocated.allocation_rate == Decimal("50.0")
