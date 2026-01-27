# -*- coding: utf-8 -*-
"""
budget_analysis_service 单元测试

测试预算与实际对比分析服务的各个方法
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.budget_analysis_service import BudgetAnalysisService


@pytest.mark.unit
class TestGetBudgetExecutionAnalysis:
    """测试 get_budget_execution_analysis 方法"""

    def test_project_not_found(self):
        """测试项目不存在"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            BudgetAnalysisService.get_budget_execution_analysis(mock_db, 999)

            assert "项目不存在" in str(exc_info.value)

    def test_no_budget(self):
        """测试没有预算"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "P001"
        mock_project.project_name = "Test Project"
        mock_project.budget_amount = Decimal('100000')
        mock_project.actual_cost = None

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
        elif model_name == 'ProjectBudget':
            query_mock.filter.return_value.order_by.return_value.first.return_value = None
        elif model_name == 'ProjectCost':
            query_mock.filter.return_value.all.return_value = []
            return query_mock

            mock_db.query.side_effect = query_side_effect

            result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)

            assert result['project_id'] == 1
            assert result['budget_amount'] == 100000.0
            assert result['actual_cost'] == 0
            assert result['warning_status'] == '正常'

    def test_with_budget_and_costs(self):
        """测试有预算和成本"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "P001"
        mock_project.project_name = "Test Project"
        mock_project.budget_amount = Decimal('100000')
        mock_project.actual_cost = None

        mock_budget = MagicMock()
        mock_budget.total_amount = Decimal('100000')
        mock_budget.version = 1
        mock_budget.budget_no = "B001"
        mock_budget.items = []

        mock_cost = MagicMock()
        mock_cost.amount = Decimal('50000')
        mock_cost.cost_category = "人工成本"

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
        elif model_name == 'ProjectBudget':
            query_mock.filter.return_value.order_by.return_value.first.return_value = mock_budget
        elif model_name == 'ProjectCost':
            query_mock.filter.return_value.all.return_value = [mock_cost]
            return query_mock

            mock_db.query.side_effect = query_side_effect

            result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)

            assert result['budget_amount'] == 100000.0
            assert result['actual_cost'] == 50000.0
            assert result['execution_rate'] == 50.0
            assert result['remaining_budget'] == 50000.0
            assert result['warning_status'] == '正常'

    def test_over_budget(self):
        """测试超预算"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "P001"
        mock_project.project_name = "Test Project"
        mock_project.budget_amount = Decimal('100000')
        mock_project.actual_cost = Decimal('120000')  # Over budget

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
        elif model_name == 'ProjectBudget':
            query_mock.filter.return_value.order_by.return_value.first.return_value = None
        elif model_name == 'ProjectCost':
            query_mock.filter.return_value.all.return_value = []
            return query_mock

            mock_db.query.side_effect = query_side_effect

            result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)

            assert result['execution_rate'] == 120.0
            assert result['warning_status'] == '超支'

    def test_warning_status(self):
        """测试警告状态"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "P001"
        mock_project.project_name = "Test Project"
        mock_project.budget_amount = Decimal('100000')
        mock_project.actual_cost = Decimal('95000')  # 95% execution

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
        elif model_name == 'ProjectBudget':
            query_mock.filter.return_value.order_by.return_value.first.return_value = None
        elif model_name == 'ProjectCost':
            query_mock.filter.return_value.all.return_value = []
            return query_mock

            mock_db.query.side_effect = query_side_effect

            result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)

            assert result['warning_status'] == '警告'

    def test_with_budget_items(self):
        """测试有预算明细"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "P001"
        mock_project.project_name = "Test Project"
        mock_project.budget_amount = Decimal('100000')
        mock_project.actual_cost = None

        mock_budget_item = MagicMock()
        mock_budget_item.cost_category = "人工成本"
        mock_budget_item.budget_amount = Decimal('50000')

        mock_budget = MagicMock()
        mock_budget.total_amount = Decimal('100000')
        mock_budget.version = 1
        mock_budget.budget_no = "B001"
        mock_budget.items = [mock_budget_item]

        mock_cost = MagicMock()
        mock_cost.amount = Decimal('30000')
        mock_cost.cost_category = "人工成本"

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
        elif model_name == 'ProjectBudget':
            query_mock.filter.return_value.order_by.return_value.first.return_value = mock_budget
        elif model_name == 'ProjectCost':
            query_mock.filter.return_value.all.return_value = [mock_cost]
            return query_mock

            mock_db.query.side_effect = query_side_effect

            result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)

            assert len(result['category_comparison']) == 1
            assert result['category_comparison'][0]['category'] == '人工成本'
            assert result['category_comparison'][0]['budget_amount'] == 50000.0
            assert result['category_comparison'][0]['actual_amount'] == 30000.0


@pytest.mark.unit
class TestGetBudgetTrendAnalysis:
    """测试 get_budget_trend_analysis 方法"""

    def test_project_not_found(self):
        """测试项目不存在"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            BudgetAnalysisService.get_budget_trend_analysis(mock_db, 999)

            assert "项目不存在" in str(exc_info.value)

    def test_no_costs(self):
        """测试没有成本记录"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.budget_amount = Decimal('100000')

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
        elif model_name == 'ProjectBudget':
            query_mock.filter.return_value.order_by.return_value.first.return_value = None
        elif model_name == 'ProjectCost':
            chain_mock = MagicMock()
            chain_mock.filter.return_value = chain_mock
            chain_mock.order_by.return_value.all.return_value = []
            query_mock.filter.return_value = chain_mock
            return query_mock

            mock_db.query.side_effect = query_side_effect

            result = BudgetAnalysisService.get_budget_trend_analysis(mock_db, 1)

            assert result['project_id'] == 1
            assert result['budget_amount'] == 100000.0
            assert result['total_actual_cost'] == 0
            assert result['monthly_trend'] == []

    def test_with_costs(self):
        """测试有成本记录"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.budget_amount = Decimal('100000')

        mock_budget = MagicMock()
        mock_budget.total_amount = Decimal('100000')

        mock_cost1 = MagicMock()
        mock_cost1.cost_date = date(2024, 1, 15)
        mock_cost1.amount = Decimal('20000')

        mock_cost2 = MagicMock()
        mock_cost2.cost_date = date(2024, 1, 20)
        mock_cost2.amount = Decimal('10000')

        mock_cost3 = MagicMock()
        mock_cost3.cost_date = date(2024, 2, 10)
        mock_cost3.amount = Decimal('15000')

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
        elif model_name == 'ProjectBudget':
            query_mock.filter.return_value.order_by.return_value.first.return_value = mock_budget
        elif model_name == 'ProjectCost':
            chain_mock = MagicMock()
            chain_mock.filter.return_value = chain_mock
            chain_mock.order_by.return_value.all.return_value = [mock_cost1, mock_cost2, mock_cost3]
            query_mock.filter.return_value = chain_mock
            return query_mock

            mock_db.query.side_effect = query_side_effect

            result = BudgetAnalysisService.get_budget_trend_analysis(mock_db, 1)

            assert result['project_id'] == 1
            assert result['total_actual_cost'] == 45000.0
            assert len(result['monthly_trend']) == 2

            # January data
            jan_data = result['monthly_trend'][0]
            assert jan_data['month'] == '2024-01'
            assert jan_data['monthly_cost'] == 30000.0
            assert jan_data['cumulative_cost'] == 30000.0

            # February data
            feb_data = result['monthly_trend'][1]
            assert feb_data['month'] == '2024-02'
            assert feb_data['monthly_cost'] == 15000.0
            assert feb_data['cumulative_cost'] == 45000.0

    def test_with_date_filter(self):
        """测试带日期过滤"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.budget_amount = Decimal('100000')

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
        elif model_name == 'ProjectBudget':
            query_mock.filter.return_value.order_by.return_value.first.return_value = None
        elif model_name == 'ProjectCost':
            chain_mock = MagicMock()
            chain_mock.filter.return_value = chain_mock
            chain_mock.order_by.return_value.all.return_value = []
            query_mock.filter.return_value = chain_mock
            return query_mock

            mock_db.query.side_effect = query_side_effect

            result = BudgetAnalysisService.get_budget_trend_analysis(
            mock_db,
            1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
            )

            assert result['project_id'] == 1


@pytest.mark.unit
class TestBudgetAnalysisIntegration:
    """集成测试"""

    def test_service_is_importable(self):
        """测试服务可导入"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        assert BudgetAnalysisService is not None

    def test_all_methods_exist(self):
        """测试所有方法存在"""
        assert hasattr(BudgetAnalysisService, 'get_budget_execution_analysis')
        assert hasattr(BudgetAnalysisService, 'get_budget_trend_analysis')

    def test_execution_rate_calculation(self):
        """测试执行率计算"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "P001"
        mock_project.project_name = "Test Project"
        mock_project.budget_amount = Decimal('200000')
        mock_project.actual_cost = Decimal('170000')  # 85% execution

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
        elif model_name == 'ProjectBudget':
            query_mock.filter.return_value.order_by.return_value.first.return_value = None
        elif model_name == 'ProjectCost':
            query_mock.filter.return_value.all.return_value = []
            return query_mock

            mock_db.query.side_effect = query_side_effect

            result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)

            assert result['execution_rate'] == 85.0
            assert result['warning_status'] == '注意'

    def test_zero_budget(self):
        """测试零预算"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "P001"
        mock_project.project_name = "Test Project"
        mock_project.budget_amount = Decimal('0')
        mock_project.actual_cost = Decimal('10000')

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
        elif model_name == 'ProjectBudget':
            query_mock.filter.return_value.order_by.return_value.first.return_value = None
        elif model_name == 'ProjectCost':
            query_mock.filter.return_value.all.return_value = []
            return query_mock

            mock_db.query.side_effect = query_side_effect

            result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)

            assert result['execution_rate'] == 0
            assert result['variance_pct'] == 0
