# -*- coding: utf-8 -*-
"""
BudgetAnalysisService 综合单元测试

测试覆盖:
- get_budget_execution_analysis: 获取项目预算执行情况分析
- get_budget_trend_analysis: 获取预算执行趋势分析
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestGetBudgetExecutionAnalysis:
    """测试 get_budget_execution_analysis 方法"""

    def test_raises_error_when_project_not_found(self):
        """测试项目不存在时抛出异常"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            BudgetAnalysisService.get_budget_execution_analysis(mock_db, project_id=999)

        assert "项目不存在" in str(exc_info.value)

    def test_returns_analysis_with_budget(self):
        """测试有预算时返回分析结果"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = Decimal("100000")
        mock_project.actual_cost = Decimal("80000")

        mock_budget = MagicMock()
        mock_budget.total_amount = Decimal("100000")
        mock_budget.version = 1
        mock_budget.budget_no = "BUD001"
        mock_budget.items = []

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_budget
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, project_id=1)

        assert result["project_id"] == 1
        assert result["budget_amount"] == 100000.0
        assert result["actual_cost"] == 80000.0
        assert result["execution_rate"] == 80.0
        assert result["warning_status"] == "注意"

    def test_uses_project_budget_when_no_budget_record(self):
        """测试无预算记录时使用项目预算"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = Decimal("50000")
        mock_project.actual_cost = Decimal("30000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, project_id=1)

        assert result["budget_amount"] == 50000.0
        assert result["budget_version"] is None

    def test_calculates_variance_correctly(self):
        """测试正确计算偏差"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = Decimal("100000")
        mock_project.actual_cost = Decimal("120000")  # 超支

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, project_id=1)

        assert result["variance"] == 20000.0  # 120000 - 100000
        assert result["variance_pct"] == 20.0
        assert result["warning_status"] == "超支"

    def test_calculates_category_comparison(self):
        """测试按类别对比"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = Decimal("100000")
        mock_project.actual_cost = None

        mock_budget_item = MagicMock()
        mock_budget_item.cost_category = "人工成本"
        mock_budget_item.budget_amount = Decimal("50000")

        mock_budget = MagicMock()
        mock_budget.total_amount = Decimal("100000")
        mock_budget.version = 1
        mock_budget.budget_no = "BUD001"
        mock_budget.items = [mock_budget_item]

        mock_cost = MagicMock()
        mock_cost.cost_category = "人工成本"
        mock_cost.amount = Decimal("45000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_budget
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_cost]

        result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, project_id=1)

        assert len(result["category_comparison"]) >= 1
        labor_category = next(
            (c for c in result["category_comparison"] if c["category"] == "人工成本"),
            None
        )
        assert labor_category is not None
        assert labor_category["budget_amount"] == 50000.0
        assert labor_category["actual_amount"] == 45000.0

    def test_returns_warning_status_for_different_thresholds(self):
        """测试不同阈值的预警状态"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        test_cases = [
            (50000, "正常"),  # 50%
            (85000, "注意"),  # 85%
            (95000, "警告"),  # 95%
            (110000, "超支"),  # 110%
        ]

        for actual_cost, expected_status in test_cases:
            mock_db = MagicMock()

            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.project_code = "PJ001"
            mock_project.project_name = "测试项目"
            mock_project.budget_amount = Decimal("100000")
            mock_project.actual_cost = Decimal(str(actual_cost))

            mock_db.query.return_value.filter.return_value.first.return_value = mock_project
            mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
            mock_db.query.return_value.filter.return_value.all.return_value = []

            result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, project_id=1)

            assert result["warning_status"] == expected_status, f"Expected {expected_status} for {actual_cost}"


class TestGetBudgetTrendAnalysis:
    """测试 get_budget_trend_analysis 方法"""

    def test_raises_error_when_project_not_found(self):
        """测试项目不存在时抛出异常"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            BudgetAnalysisService.get_budget_trend_analysis(mock_db, project_id=999)

        assert "项目不存在" in str(exc_info.value)

    def test_returns_trend_data(self):
        """测试返回趋势数据"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.budget_amount = Decimal("100000")

        mock_budget = MagicMock()
        mock_budget.total_amount = Decimal("100000")

        mock_cost = MagicMock()
        mock_cost.cost_date = date.today()
        mock_cost.amount = Decimal("10000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_budget
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_cost]

        result = BudgetAnalysisService.get_budget_trend_analysis(mock_db, project_id=1)

        assert result["project_id"] == 1
        assert result["budget_amount"] == 100000.0
        assert "monthly_trend" in result

    def test_groups_costs_by_month(self):
        """测试按月分组成本"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.budget_amount = Decimal("100000")

        today = date.today()
        last_month = today.replace(day=1) - timedelta(days=1)

        mock_cost1 = MagicMock()
        mock_cost1.cost_date = today
        mock_cost1.amount = Decimal("10000")

        mock_cost2 = MagicMock()
        mock_cost2.cost_date = last_month
        mock_cost2.amount = Decimal("20000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_cost1,
            mock_cost2,
        ]

        result = BudgetAnalysisService.get_budget_trend_analysis(mock_db, project_id=1)

        assert result["total_actual_cost"] == 30000.0

    def test_calculates_cumulative_cost(self):
        """测试计算累计成本"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.budget_amount = Decimal("100000")

        today = date.today()
        last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=15)
        two_months_ago = (last_month.replace(day=1) - timedelta(days=1)).replace(day=15)

        mock_cost1 = MagicMock()
        mock_cost1.cost_date = two_months_ago
        mock_cost1.amount = Decimal("10000")

        mock_cost2 = MagicMock()
        mock_cost2.cost_date = last_month
        mock_cost2.amount = Decimal("15000")

        mock_cost3 = MagicMock()
        mock_cost3.cost_date = today
        mock_cost3.amount = Decimal("5000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_cost1,
            mock_cost2,
            mock_cost3,
        ]

        result = BudgetAnalysisService.get_budget_trend_analysis(mock_db, project_id=1)

        # 累计成本应该递增
        if len(result["monthly_trend"]) >= 2:
            for i in range(1, len(result["monthly_trend"])):
                assert result["monthly_trend"][i]["cumulative_cost"] >= result["monthly_trend"][i-1]["cumulative_cost"]

    def test_filters_by_date_range(self):
        """测试按日期范围筛选"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.budget_amount = Decimal("100000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []

        start_date = date.today() - timedelta(days=90)
        end_date = date.today()

        result = BudgetAnalysisService.get_budget_trend_analysis(
            mock_db,
            project_id=1,
            start_date=start_date,
            end_date=end_date
        )

        assert result["project_id"] == 1

    def test_handles_empty_costs(self):
        """测试处理空成本记录"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.budget_amount = Decimal("100000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = BudgetAnalysisService.get_budget_trend_analysis(mock_db, project_id=1)

        assert result["total_actual_cost"] == 0
        assert result["monthly_trend"] == []

    def test_calculates_execution_rate_per_month(self):
        """测试计算每月执行率"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.budget_amount = Decimal("100000")

        mock_cost = MagicMock()
        mock_cost.cost_date = date.today()
        mock_cost.amount = Decimal("50000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_cost]

        result = BudgetAnalysisService.get_budget_trend_analysis(mock_db, project_id=1)

        if result["monthly_trend"]:
            current_month = result["monthly_trend"][-1]
            assert current_month["execution_rate"] == 50.0  # 50000/100000 * 100

    def test_handles_zero_budget(self):
        """测试处理零预算"""
        from app.services.budget_analysis_service import BudgetAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.budget_amount = Decimal("0")

        mock_cost = MagicMock()
        mock_cost.cost_date = date.today()
        mock_cost.amount = Decimal("10000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_cost]

        result = BudgetAnalysisService.get_budget_trend_analysis(mock_db, project_id=1)

        # 零预算时执行率应该为0
        if result["monthly_trend"]:
            assert result["monthly_trend"][-1]["execution_rate"] == 0
