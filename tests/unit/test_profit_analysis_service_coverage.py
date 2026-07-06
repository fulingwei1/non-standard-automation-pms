# -*- coding: utf-8 -*-
"""profit_analysis_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.profit_analysis_service import ProfitAnalysisService

class TestProfitAnalysisServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProfitAnalysisService(mock_db)
        assert hasattr(service, 'db')


def _project(contract=100000, budget=80000):
    p = Mock()
    p.id = 1
    p.contract_amount = contract
    p.budget_amount = budget
    return p


def _service_with_project(project):
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = project
    return ProfitAnalysisService(mock_db), mock_db


class TestProfitAnalysisServiceExtraCoverage:
    def test_calculate_project_profit_with_forecast(self):
        service, _ = _service_with_project(_project())
        service._get_actual_cost = Mock(return_value=50000)

        result = service.calculate_project_profit(1)

        assert result["actual_profit"] == 50000
        assert result["forecast_profit"] == 20000
        assert result["has_forecast"] is True

    def test_calculate_project_profit_no_project(self):
        service, _ = _service_with_project(None)

        assert service.calculate_project_profit(99) == {"error": "项目不存在"}

    def test_calculate_gross_margin_actual_and_forecast(self):
        service, _ = _service_with_project(_project())
        service._get_actual_cost = Mock(return_value=50000)

        actual = service.calculate_gross_margin(1)
        forecast = service.calculate_gross_margin(1, use_forecast=True)

        assert actual["gross_margin_rate"] == 50.0
        assert actual["is_forecast"] is False
        assert forecast["gross_margin_rate"] == 20.0
        assert forecast["is_forecast"] is True

    def test_calculate_gross_margin_invalid_contract(self):
        service, _ = _service_with_project(_project(contract=0))

        assert service.calculate_gross_margin(1) == {"error": "合同金额无效"}

    def test_allocate_costs_default_distribution(self):
        service, _ = _service_with_project(_project())
        service._get_actual_cost = Mock(return_value=100000)
        service._get_cost_by_type = Mock(return_value={"材料": 60000, "人工": 40000})

        result = service.allocate_costs(1, {})

        assert result["total_cost"] == 100000
        assert result["unallocated"] == 0
        assert len(result["allocated_costs"]) == 2

    def test_allocate_costs_ratio_and_fixed_amount(self):
        service, _ = _service_with_project(_project())
        service._get_actual_cost = Mock(return_value=100000)

        result = service.allocate_costs(1, {"材料": 0.6, "人工": 30000})

        assert result["allocated_costs"] == [
            {"category": "材料", "amount": 60000.0},
            {"category": "人工", "amount": 30000},
        ]
        assert result["unallocated"] == 10000.0

    def test_allocate_costs_no_project(self):
        service, _ = _service_with_project(None)

        assert service.allocate_costs(99, {"材料": 0.5}) == {"error": "项目不存在"}
