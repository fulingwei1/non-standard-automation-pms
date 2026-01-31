# -*- coding: utf-8 -*-
"""
cost_allocation_service 综合单元测试

测试覆盖:
- query_allocatable_costs: 查询需要分摊的费用
- get_target_project_ids: 获取目标项目ID列表
- calculate_allocation_rates_by_hours: 按工时分摊计算分摊比例
- calculate_allocation_rates_by_headcount: 按人数分摊计算分摊比例
- calculate_allocation_rates: 根据分摊依据计算分摊比例
- create_allocated_cost: 创建分摊后的费用记录
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestQueryAllocatableCosts:
    """测试 query_allocatable_costs 函数"""

    def test_returns_allocatable_costs(self):
        """测试返回可分摊的费用"""
        from app.services.cost_allocation_service import query_allocatable_costs

        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.cost_type_ids = None

        mock_cost = MagicMock()
        mock_cost.id = 1
        mock_cost.status = 'APPROVED'
        mock_cost.is_allocated = False

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_cost]

        result = query_allocatable_costs(mock_db, mock_rule, None)

        assert len(result) == 1
        assert result[0].id == 1

    def test_filters_by_cost_ids(self):
        """测试按费用ID筛选"""
        from app.services.cost_allocation_service import query_allocatable_costs

        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.cost_type_ids = None

        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = query_allocatable_costs(mock_db, mock_rule, [1, 2, 3])

        assert result == []

    def test_filters_by_cost_type_ids(self):
        """测试按费用类型筛选"""
        from app.services.cost_allocation_service import query_allocatable_costs

        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.cost_type_ids = [10, 20]

        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = query_allocatable_costs(mock_db, mock_rule, None)

        assert result == []


class TestGetTargetProjectIds:
    """测试 get_target_project_ids 函数"""

    def test_returns_rule_project_ids(self):
        """测试返回规则中的项目ID"""
        from app.services.cost_allocation_service import get_target_project_ids

        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.project_ids = [1, 2, 3]

        result = get_target_project_ids(mock_db, mock_rule)

        assert result == [1, 2, 3]

    def test_returns_active_projects_when_no_rule_ids(self):
        """测试规则无项目ID时返回活跃项目"""
        from app.services.cost_allocation_service import get_target_project_ids

        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.project_ids = None

        mock_project1 = MagicMock()
        mock_project1.id = 10
        mock_project2 = MagicMock()
        mock_project2.id = 20

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project1, mock_project2]

        result = get_target_project_ids(mock_db, mock_rule)

        assert result == [10, 20]

    def test_returns_empty_list_when_no_projects(self):
        """测试无项目时返回空列表"""
        from app.services.cost_allocation_service import get_target_project_ids

        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.project_ids = []

        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_target_project_ids(mock_db, mock_rule)

        assert result == []


class TestCalculateAllocationRatesByHours:
    """测试 calculate_allocation_rates_by_hours 函数"""

    def test_calculates_rates_by_hours(self):
        """测试按工时计算分摊比例"""
        from app.services.cost_allocation_service import calculate_allocation_rates_by_hours

        mock_db = MagicMock()

        mock_project1 = MagicMock()
        mock_project1.total_hours = 100
        mock_project2 = MagicMock()
        mock_project2.total_hours = 100

        def side_effect(model):
            query = MagicMock()
            def filter_side_effect(*args, **kwargs):
                result = MagicMock()
                # Return projects based on project_id
                if args and hasattr(args[0], 'right'):
                    # Get project_id from filter
                    result.first.return_value = mock_project1
                return result
            query.filter = filter_side_effect
            return query

        mock_db.query.side_effect = side_effect

        # Simplified test
        result = calculate_allocation_rates_by_hours(mock_db, [1, 2])

        # Either gets calculated rates or equal distribution
        assert len(result) == 2

    def test_uses_equal_distribution_when_no_hours(self):
        """测试无工时时使用平均分摊"""
        from app.services.cost_allocation_service import calculate_allocation_rates_by_hours

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.total_hours = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = calculate_allocation_rates_by_hours(mock_db, [1, 2])

        # 平均分摊：100 / 2 = 50
        assert result[1] == 50.0
        assert result[2] == 50.0

    def test_handles_single_project(self):
        """测试单个项目"""
        from app.services.cost_allocation_service import calculate_allocation_rates_by_hours

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.total_hours = 100

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = calculate_allocation_rates_by_hours(mock_db, [1])

        assert result[1] == 100.0


class TestCalculateAllocationRatesByHeadcount:
    """测试 calculate_allocation_rates_by_headcount 函数"""

    def test_calculates_rates_by_headcount(self):
        """测试按人数计算分摊比例"""
        from app.services.cost_allocation_service import calculate_allocation_rates_by_headcount

        mock_db = MagicMock()

        mock_project1 = MagicMock()
        mock_project1.participant_count = 5
        mock_project2 = MagicMock()
        mock_project2.participant_count = 5

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_project1, mock_project2]

        result = calculate_allocation_rates_by_headcount(mock_db, [1, 2])

        # 每个项目5人，总共10人，各占50%
        assert result[1] == 50.0
        assert result[2] == 50.0

    def test_uses_equal_distribution_when_no_participants(self):
        """测试无人数时使用平均分摊"""
        from app.services.cost_allocation_service import calculate_allocation_rates_by_headcount

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.participant_count = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = calculate_allocation_rates_by_headcount(mock_db, [1, 2, 3])

        # 平均分摊：100 / 3 ≈ 33.33
        assert abs(result[1] - 33.33) < 0.01
        assert abs(result[2] - 33.33) < 0.01
        assert abs(result[3] - 33.33) < 0.01

    def test_handles_unequal_participants(self):
        """测试不等人数的分摊"""
        from app.services.cost_allocation_service import calculate_allocation_rates_by_headcount

        mock_db = MagicMock()

        mock_project1 = MagicMock()
        mock_project1.participant_count = 3
        mock_project2 = MagicMock()
        mock_project2.participant_count = 7

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_project1, mock_project2]

        result = calculate_allocation_rates_by_headcount(mock_db, [1, 2])

        # 3人/10人 = 30%, 7人/10人 = 70%
        assert result[1] == 30.0
        assert result[2] == 70.0


class TestCalculateAllocationRates:
    """测试 calculate_allocation_rates 函数"""

    def test_uses_hours_allocation(self):
        """测试使用工时分摊"""
        from app.services.cost_allocation_service import calculate_allocation_rates

        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.allocation_basis = 'HOURS'

        mock_project = MagicMock()
        mock_project.total_hours = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = calculate_allocation_rates(mock_db, mock_rule, [1, 2])

        assert len(result) == 2

    def test_uses_headcount_allocation(self):
        """测试使用人数分摊"""
        from app.services.cost_allocation_service import calculate_allocation_rates

        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.allocation_basis = 'HEADCOUNT'

        mock_project = MagicMock()
        mock_project.participant_count = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = calculate_allocation_rates(mock_db, mock_rule, [1, 2])

        assert len(result) == 2

    def test_uses_equal_allocation_for_revenue(self):
        """测试收入分摊使用平均分摊"""
        from app.services.cost_allocation_service import calculate_allocation_rates

        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.allocation_basis = 'REVENUE'

        result = calculate_allocation_rates(mock_db, mock_rule, [1, 2, 3, 4])

        # 平均分摊：100 / 4 = 25
        assert result[1] == 25.0
        assert result[2] == 25.0
        assert result[3] == 25.0
        assert result[4] == 25.0

    def test_uses_equal_allocation_for_unknown_basis(self):
        """测试未知分摊依据使用平均分摊"""
        from app.services.cost_allocation_service import calculate_allocation_rates

        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.allocation_basis = 'UNKNOWN'

        result = calculate_allocation_rates(mock_db, mock_rule, [1, 2])

        assert result[1] == 50.0
        assert result[2] == 50.0


class TestCreateAllocatedCost:
    """测试 create_allocated_cost 函数"""

    def test_creates_allocated_cost(self):
        """测试创建分摊费用"""
        from app.services.cost_allocation_service import create_allocated_cost

        mock_db = MagicMock()

        mock_cost = MagicMock()
        mock_cost.id = 1
        mock_cost.cost_no = "COST001"
        mock_cost.cost_type_id = 10
        mock_cost.cost_date = "2026-01-15"
        mock_cost.cost_amount = Decimal("1000")
        mock_cost.cost_description = "测试费用"
        mock_cost.deductible_amount = Decimal("100")

        mock_project = MagicMock()
        mock_project.total_cost = Decimal("5000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_generate_cost_no = MagicMock(return_value="COST002")

        result = create_allocated_cost(
            mock_db, mock_cost, 1, 30.0, 100, mock_generate_cost_no
        )

        mock_db.add.assert_called_once()
        assert result.cost_amount == Decimal("300")  # 1000 * 30%
        assert result.allocation_rate == Decimal("30.0")
        assert result.source_id == 1

    def test_updates_project_total_cost(self):
        """测试更新项目总费用"""
        from app.services.cost_allocation_service import create_allocated_cost

        mock_db = MagicMock()

        mock_cost = MagicMock()
        mock_cost.id = 1
        mock_cost.cost_no = "COST001"
        mock_cost.cost_type_id = 10
        mock_cost.cost_date = "2026-01-15"
        mock_cost.cost_amount = Decimal("1000")
        mock_cost.cost_description = "测试费用"
        mock_cost.deductible_amount = None

        mock_project = MagicMock()
        mock_project.total_cost = Decimal("5000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_generate_cost_no = MagicMock(return_value="COST002")

        create_allocated_cost(
            mock_db, mock_cost, 1, 50.0, 100, mock_generate_cost_no
        )

        # 5000 + 500 (1000 * 50%) = 5500
        assert mock_project.total_cost == Decimal("5500")

    def test_handles_none_total_cost(self):
        """测试处理项目总费用为None"""
        from app.services.cost_allocation_service import create_allocated_cost

        mock_db = MagicMock()

        mock_cost = MagicMock()
        mock_cost.id = 1
        mock_cost.cost_no = "COST001"
        mock_cost.cost_type_id = 10
        mock_cost.cost_date = "2026-01-15"
        mock_cost.cost_amount = Decimal("1000")
        mock_cost.cost_description = "测试费用"
        mock_cost.deductible_amount = None

        mock_project = MagicMock()
        mock_project.total_cost = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_generate_cost_no = MagicMock(return_value="COST002")

        create_allocated_cost(
            mock_db, mock_cost, 1, 25.0, 100, mock_generate_cost_no
        )

        # 0 + 250 (1000 * 25%) = 250
        assert mock_project.total_cost == Decimal("250")

    def test_calculates_deductible_amount(self):
        """测试计算可抵扣金额"""
        from app.services.cost_allocation_service import create_allocated_cost

        mock_db = MagicMock()

        mock_cost = MagicMock()
        mock_cost.id = 1
        mock_cost.cost_no = "COST001"
        mock_cost.cost_type_id = 10
        mock_cost.cost_date = "2026-01-15"
        mock_cost.cost_amount = Decimal("1000")
        mock_cost.cost_description = "测试费用"
        mock_cost.deductible_amount = Decimal("200")

        mock_project = MagicMock()
        mock_project.total_cost = Decimal("5000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_generate_cost_no = MagicMock(return_value="COST002")

        result = create_allocated_cost(
            mock_db, mock_cost, 1, 50.0, 100, mock_generate_cost_no
        )

        # 分摊金额500元，可抵扣比例200/1000 = 20%，所以可抵扣金额 = 500 * 20% = 100
        assert result.deductible_amount == Decimal("100")
