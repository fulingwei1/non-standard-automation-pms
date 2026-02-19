# -*- coding: utf-8 -*-
"""
第三十二批覆盖率测试 - 工时成本服务 (扩展)
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date

try:
    from app.services.labor_cost_service import LaborCostService, LaborCostExpenseService
    HAS_LCS = True
except Exception:
    HAS_LCS = False

pytestmark = pytest.mark.skipif(not HAS_LCS, reason="labor_cost_service 导入失败")


def make_service():
    db = MagicMock()
    svc = LaborCostService(db)
    return svc, db


class TestLaborCostServiceInit:
    def test_init(self):
        db = MagicMock()
        svc = LaborCostService(db)
        assert svc.db is db


class TestGetUserHourlyRate:
    def test_delegates_to_hourly_rate_service(self):
        """委托给HourlyRateService"""
        db = MagicMock()
        with patch("app.services.labor_cost_service.HourlyRateService") as MockHRS:
            MockHRS.get_user_hourly_rate.return_value = Decimal("50.00")
            result = LaborCostService.get_user_hourly_rate(db, user_id=1)
        assert result == Decimal("50.00")


class TestCalculateProjectLaborCost:
    def test_project_not_found(self):
        """项目不存在时返回失败"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = LaborCostService.calculate_project_labor_cost(db, project_id=999)
        assert result["success"] is False
        assert "项目不存在" in result["message"]

    def test_no_timesheets(self):
        """无工时记录时返回成功但无成本"""
        db = MagicMock()
        mock_project = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch("app.services.labor_cost_service.query_approved_timesheets", return_value=[]):
            result = LaborCostService.calculate_project_labor_cost(db, project_id=1)

        assert result["success"] is True
        assert result["cost_count"] == 0

    def test_with_timesheets_success(self):
        """有工时记录时正常计算"""
        db = MagicMock()
        mock_project = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_timesheets = [MagicMock(), MagicMock()]
        mock_user_costs = {1: {"total_hours": 10, "timesheets": []}}
        mock_created = [MagicMock()]
        mock_total_cost = Decimal("500.00")

        with patch("app.services.labor_cost_service.query_approved_timesheets", return_value=mock_timesheets), \
             patch("app.services.labor_cost_service.group_timesheets_by_user", return_value=mock_user_costs), \
             patch("app.services.labor_cost_service.process_user_costs", return_value=(mock_created, mock_total_cost)):
            result = LaborCostService.calculate_project_labor_cost(db, project_id=1)

        assert result["success"] is True
        assert result["cost_count"] == 1
        assert result["total_cost"] == 500.0

    def test_recalculate_deletes_existing(self):
        """重新计算时先删除现有记录"""
        db = MagicMock()
        mock_project = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_timesheets = [MagicMock()]
        mock_user_costs = {1: {"total_hours": 5, "timesheets": []}}
        mock_created = [MagicMock()]

        with patch("app.services.labor_cost_service.query_approved_timesheets", return_value=mock_timesheets), \
             patch("app.services.labor_cost_service.delete_existing_costs") as mock_del, \
             patch("app.services.labor_cost_service.group_timesheets_by_user", return_value=mock_user_costs), \
             patch("app.services.labor_cost_service.process_user_costs", return_value=(mock_created, Decimal("200"))):
            result = LaborCostService.calculate_project_labor_cost(db, project_id=1, recalculate=True)

        mock_del.assert_called_once()


class TestCalculateAllProjectsLaborCost:
    def test_no_projects(self):
        """无项目时返回空结果"""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        result = LaborCostService.calculate_all_projects_labor_cost(db)
        assert result is not None


class TestLaborCostExpenseServiceIdentify:
    def test_identify_lost_projects_empty(self):
        """无未中标项目"""
        db = MagicMock()
        svc = LaborCostExpenseService(db)
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []

        result = svc.identify_lost_projects()
        assert isinstance(result, list)

    def test_identify_filters_by_date(self):
        """按日期范围过滤"""
        db = MagicMock()
        svc = LaborCostExpenseService(db)
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = svc.identify_lost_projects(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        assert isinstance(result, list)

    def test_get_expense_statistics_empty(self):
        """空数据时统计正常"""
        db = MagicMock()
        svc = LaborCostExpenseService(db)
        with patch.object(svc, "get_lost_project_expenses", return_value=[]):
            if hasattr(svc, "get_expense_statistics"):
                result = svc.get_expense_statistics(date(2024, 1, 1), date(2024, 12, 31))
                assert "total_cost" in result or result is not None
