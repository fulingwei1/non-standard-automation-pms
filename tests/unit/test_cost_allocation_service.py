# -*- coding: utf-8 -*-
"""
费用分摊服务测试
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.models.rd_project import RdProject
from app.services.cost_allocation_service import (
    calculate_allocation_rates,
    calculate_allocation_rates_by_headcount,
    calculate_allocation_rates_by_hours,
    create_allocated_cost,
    get_target_project_ids,
    query_allocatable_costs,
)


class TestQueryAllocatableCosts:
    """测试 query_allocatable_costs 函数"""

    def test_query_all_allocatable_costs_without_cost_ids(self):
        """测试不指定费用ID时，查询所有可分摊费用"""
        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.cost_type_ids = [1, 2, 3]

        # Mock query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
        MagicMock(id=1, status="APPROVED", is_allocated=False),
        MagicMock(id=2, status="APPROVED", is_allocated=False),
        ]
        mock_db.query.return_value = mock_query

        result = query_allocatable_costs(mock_db, mock_rule, None)

        assert len(result) == 2
        # Verify filters were applied
        assert mock_query.filter.call_count == 2  # status filter + cost_type filter

    def test_query_with_specific_cost_ids(self):
        """测试指定费用ID时，只查询指定的费用"""
        mock_db = MagicMock()
        mock_rule = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
        MagicMock(id=1, status="APPROVED", is_allocated=False),
        ]
        mock_db.query.return_value = mock_query

        result = query_allocatable_costs(mock_db, mock_rule, [1, 2, 3])

        assert len(result) == 1
        # Verify cost_ids filter was applied
        assert mock_query.filter.call_count == 2

    def test_query_without_cost_ids_and_rule_without_cost_types(self):
        """测试规则没有指定费用类型时，查询所有符合条件的费用"""
        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.cost_type_ids = None

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
        MagicMock(id=1, status="APPROVED", is_allocated=False),
        ]
        mock_db.query.return_value = mock_query

        result = query_allocatable_costs(mock_db, mock_rule, None)

        assert len(result) == 1
        # Only one filter applied (with 2 conditions: status and is_allocated)
        assert mock_query.filter.call_count == 1


class TestGetTargetProjectIds:
    """测试 get_target_project_ids 函数"""

    def test_get_target_ids_from_rule(self):
        """测试从规则中获取目标项目ID"""
        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.project_ids = [1, 2, 3]

        result = get_target_project_ids(mock_db, mock_rule)

        assert result == [1, 2, 3]
        mock_db.query.assert_not_called()

    def test_get_target_ids_from_db_query(self):
        """测试从数据库查询目标项目ID"""
        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.project_ids = []

        mock_query = MagicMock()
        mock_project1 = MagicMock(id=1, status="APPROVED")
        mock_project2 = MagicMock(id=2, status="IN_PROGRESS")
        mock_query.filter.return_value.all.return_value = [
        mock_project1,
        mock_project2,
        ]
        mock_db.query.return_value = mock_query

        result = get_target_project_ids(mock_db, mock_rule)

        assert result == [1, 2]


class TestCalculateAllocationRatesByHours:
    """测试 calculate_allocation_rates_by_hours 函数"""

    def test_calculate_by_hours_with_valid_projects(self):
        """测试有工时数据的项目分摊比例计算"""
        mock_db = MagicMock()
        target_project_ids = [1, 2]

        # Mock projects
        mock_project1 = MagicMock(spec=RdProject)
        type(mock_project1).total_hours = property(lambda self: Decimal("100"))
        type(mock_project1).id = property(lambda self: 1)
        mock_project2 = MagicMock(spec=RdProject)
        type(mock_project2).total_hours = property(lambda self: Decimal("200"))
        type(mock_project2).id = property(lambda self: 2)

        mock_query = MagicMock()
        mock_query.filter.side_effect = [
        MagicMock(first=mock_project1),
        MagicMock(first=mock_project2),
        ]
        mock_db.query.return_value = mock_query

        result = calculate_allocation_rates_by_hours(mock_db, target_project_ids)

        assert result[1] == pytest.approx(33.33, rel=0.01)  # 100/300 * 100
        assert result[2] == pytest.approx(66.67, rel=0.01)  # 200/300 * 100

    def test_calculate_by_hours_with_zero_total_hours(self):
        """测试总工时为0时平均分摊"""
        mock_db = MagicMock()
        target_project_ids = [1, 2, 3]

        # Mock projects with zero or None hours
        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.total_hours = 0
        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.total_hours = None
        mock_project3 = MagicMock()
        mock_project3.id = 3
        mock_project3.total_hours = 0

        mock_query = MagicMock()
        mock_query.filter.side_effect = [
        MagicMock(first=mock_project1),
        MagicMock(first=mock_project2),
        MagicMock(first=mock_project3),
        ]
        mock_db.query.return_value = mock_query

        result = calculate_allocation_rates_by_hours(mock_db, target_project_ids)

        # Should distribute evenly: 100% / 3
        assert result[1] == pytest.approx(33.33, rel=0.01)
        assert result[2] == pytest.approx(33.33, rel=0.01)
        assert result[3] == pytest.approx(33.33, rel=0.01)

    def test_calculate_by_hours_with_missing_projects(self):
        """测试部分项目不存在时的处理"""
        mock_db = MagicMock()
        target_project_ids = [1, 2, 3]

        # Only project 1 and 3 exist
        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.total_hours = Decimal("100")
        mock_project3 = MagicMock()
        mock_project3.id = 3
        mock_project3.total_hours = Decimal("100")

        mock_query = MagicMock()
        mock_query.filter.side_effect = [
        MagicMock(first=mock_project1),
        MagicMock(first=None),  # Project 2 doesn't exist
        MagicMock(first=mock_project3),
        ]
        mock_db.query.return_value = mock_query

        result = calculate_allocation_rates_by_hours(mock_db, target_project_ids)

        # Only existing projects should get allocation
        assert result[1] == pytest.approx(50.0, rel=0.01)
        assert result[3] == pytest.approx(50.0, rel=0.01)
        assert 2 not in result  # Project 2 should not be in result


class TestCalculateAllocationRatesByHeadcount:
    """测试 calculate_allocation_rates_by_headcount 函数"""

    def test_calculate_by_headcount_with_valid_projects(self):
        """测试有人员数据的项目分摊比例计算"""
        mock_db = MagicMock()
        target_project_ids = [1, 2]

        # Mock projects
        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.participant_count = 5
        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.participant_count = 10

        mock_query = MagicMock()
        mock_query.filter.side_effect = [
        MagicMock(first=mock_project1),
        MagicMock(first=mock_project2),
        ]
        mock_db.query.return_value = mock_query

        result = calculate_allocation_rates_by_headcount(mock_db, target_project_ids)

        assert result[1] == pytest.approx(33.33, rel=0.01)  # 5/15 * 100
        assert result[2] == pytest.approx(66.67, rel=0.01)  # 10/15 * 100

    def test_calculate_by_headcount_with_zero_total_headcount(self):
        """测试总人数为0时平均分摊"""
        mock_db = MagicMock()
        target_project_ids = [1, 2]

        # Mock projects with zero or None participants
        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.participant_count = 0
        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.participant_count = None

        mock_query = MagicMock()
        mock_query.filter.side_effect = [
        MagicMock(first=mock_project1),
        MagicMock(first=mock_project2),
        ]
        mock_db.query.return_value = mock_query

        result = calculate_allocation_rates_by_headcount(mock_db, target_project_ids)

        # Should distribute evenly: 100% / 2
        assert result[1] == pytest.approx(50.0, rel=0.01)
        assert result[2] == pytest.approx(50.0, rel=0.01)


class TestCalculateAllocationRates:
    """测试 calculate_allocation_rates 函数"""

    def test_calculate_by_hours_basis(self):
        """测试按工时分摊"""
        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.allocation_basis = "HOURS"
        target_project_ids = [1, 2]

        # Mock the helper function
        with patch(
        "app.services.cost_allocation_service.calculate_allocation_rates_by_hours",
        return_value={1: 50.0, 2: 50.0},
        ):
        result = calculate_allocation_rates(mock_db, mock_rule, target_project_ids)

        assert result == {1: 50.0, 2: 50.0}

    def test_calculate_by_revenue_basis(self):
        """测试按收入分摊（使用平均分摊）"""
        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.allocation_basis = "REVENUE"
        target_project_ids = [1, 2, 3]

        result = calculate_allocation_rates(mock_db, mock_rule, target_project_ids)

        # Should distribute evenly: 100% / 3
        assert result[1] == pytest.approx(33.33, rel=0.01)
        assert result[2] == pytest.approx(33.33, rel=0.01)
        assert result[3] == pytest.approx(33.33, rel=0.01)

    def test_calculate_by_headcount_basis(self):
        """测试按人数分摊"""
        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.allocation_basis = "HEADCOUNT"
        target_project_ids = [1, 2]

        with patch(
        "app.services.cost_allocation_service.calculate_allocation_rates_by_headcount",
        return_value={1: 40.0, 2: 60.0},
        ):
        result = calculate_allocation_rates(mock_db, mock_rule, target_project_ids)

        assert result == {1: 40.0, 2: 60.0}

    def test_calculate_with_unknown_basis(self):
        """测试未知分摊依据时使用平均分摊"""
        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.allocation_basis = "UNKNOWN_BASIS"
        target_project_ids = [1, 2, 3]

        result = calculate_allocation_rates(mock_db, mock_rule, target_project_ids)

        # Should distribute evenly
        assert result[1] == pytest.approx(33.33, rel=0.01)
        assert result[2] == pytest.approx(33.33, rel=0.01)
        assert result[3] == pytest.approx(33.33, rel=0.01)


class TestCreateAllocatedCost:
    """测试 create_allocated_cost 函数"""

    def test_create_allocated_cost_successfully(self):
        """测试成功创建分摊费用"""
        mock_db = MagicMock()
        mock_cost = MagicMock()
        mock_cost.cost_amount = Decimal("1000")
        mock_cost.cost_no = "COST001"
        mock_cost.cost_description = "Test cost"
        mock_cost.deductible_amount = None
        mock_cost.cost_date = "2024-01-01"
        mock_cost.cost_type_id = 1

        mock_project = MagicMock()
        mock_project.total_cost = Decimal("5000")

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value = mock_query

        result = create_allocated_cost(
        mock_db,
        mock_cost,
        project_id=1,
        rate=25.0,
        rule_id=10,
        generate_cost_no=lambda db: "ALLOC001",
        )

        # Verify the allocated cost properties
        assert result.cost_no == "ALLOC001"
        assert result.rd_project_id == 1
        assert result.cost_type_id == 1
        assert result.cost_amount == pytest.approx(
        Decimal("250"), rel=0.01
        )  # 1000 * 25% / 100
        assert result.source_type == "ALLOCATED"
        assert result.source_id == mock_cost.id
        assert result.is_allocated is True
        assert result.allocation_rule_id == 10
        assert result.allocation_rate == pytest.approx(Decimal("25"), rel=0.01)
        assert result.status == "APPROVED"

        # Verify project total cost was updated
        assert mock_project.total_cost == pytest.approx(Decimal("5250"), rel=0.01)

        # Verify db.add was called
        mock_db.add.assert_called_once()

    def test_create_allocated_cost_with_deductible_amount(self):
        """测试包含可抵扣金额的分摊费用"""
        mock_db = MagicMock()
        mock_cost = MagicMock()
        mock_cost.cost_amount = Decimal("1000")
        mock_cost.deductible_amount = Decimal("100")
        mock_cost.cost_no = "COST001"
        mock_cost.cost_description = "Test cost"
        mock_cost.cost_date = "2024-01-01"
        mock_cost.cost_type_id = 1

        mock_project = MagicMock()
        mock_project.total_cost = Decimal("0")

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value = mock_query

        result = create_allocated_cost(
        mock_db,
        mock_cost,
        project_id=1,
        rate=25.0,
        rule_id=10,
        generate_cost_no=lambda db: "ALLOC001",
        )

        # Allocated amount: 1000 * 25% = 250
        # Deductible ratio: 100/1000 = 10%
        # Allocated deductible: 250 * 10% = 25
        assert result.deductible_amount == pytest.approx(Decimal("25"), rel=0.01)
        assert result.cost_amount == pytest.approx(Decimal("250"), rel=0.01)

    def test_create_allocated_cost_without_project(self):
        """测试项目不存在时的处理"""
        mock_db = MagicMock()
        mock_cost = MagicMock()
        mock_cost.cost_amount = Decimal("1000")
        mock_cost.cost_no = "COST001"
        mock_cost.cost_description = "Test cost"
        mock_cost.deductible_amount = None
        mock_cost.cost_date = "2024-01-01"
        mock_cost.cost_type_id = 1

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None  # Project not found
        mock_db.query.return_value = mock_query

        result = create_allocated_cost(
        mock_db,
        mock_cost,
        project_id=1,
        rate=25.0,
        rule_id=10,
        generate_cost_no=lambda db: "ALLOC001",
        )

        # Should still create the cost, just won't update project total
        assert result.cost_amount == pytest.approx(Decimal("250"), rel=0.01)
        mock_db.add.assert_called_once()

    def test_create_allocated_cost_zero_rate(self):
        """测试零分摊比例"""
        mock_db = MagicMock()
        mock_cost = MagicMock()
        mock_cost.cost_amount = Decimal("1000")
        mock_cost.cost_no = "COST001"
        mock_cost.cost_description = "Test cost"
        mock_cost.deductible_amount = None
        mock_cost.cost_date = "2024-01-01"
        mock_cost.cost_type_id = 1

        mock_project = MagicMock()
        mock_project.total_cost = Decimal("5000")

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value = mock_query

        result = create_allocated_cost(
        mock_db,
        mock_cost,
        project_id=1,
        rate=0.0,
        rule_id=10,
        generate_cost_no=lambda db: "ALLOC001",
        )

        assert result.cost_amount == Decimal("0")
        mock_db.add.assert_called_once()
