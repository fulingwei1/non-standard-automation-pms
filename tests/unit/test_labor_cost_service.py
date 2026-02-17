# -*- coding: utf-8 -*-
"""
工时成本服务单元测试
覆盖批量计算、月度统计、项目不存在等核心路径
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.labor_cost_service import LaborCostService, LaborCostExpenseService


class TestCalculateProjectLaborCostNoProject:
    """项目不存在的处理"""

    def test_returns_failure_when_project_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = LaborCostService.calculate_project_labor_cost(db, project_id=999)
        assert result["success"] is False
        assert "项目不存在" in result["message"]


class TestCalculateProjectLaborCostNoTimesheets:
    """没有工时记录的处理"""

    def test_returns_empty_cost_when_no_timesheets(self):
        db = MagicMock()
        # 项目存在
        db.query.return_value.filter.return_value.first.return_value = MagicMock()

        # 函数内部 lazy import，需要 patch 工具函数所在的模块
        with patch(
            "app.services.labor_cost.utils.query_approved_timesheets",
            return_value=[],
        ), patch(
            "app.services.labor_cost_service.query_approved_timesheets",
            create=True,
            return_value=[],
        ):
            # 直接模拟内部import的函数
            import app.services.labor_cost.utils as utils_mod
            orig = getattr(utils_mod, "query_approved_timesheets", None)
            utils_mod.query_approved_timesheets = MagicMock(return_value=[])
            try:
                result = LaborCostService.calculate_project_labor_cost(db, project_id=1)
            finally:
                if orig is not None:
                    utils_mod.query_approved_timesheets = orig

        assert result["success"] is True
        assert result["cost_count"] == 0
        assert result["total_cost"] == 0


class TestCalculateProjectLaborCostWithTimesheets:
    """有工时记录的正常路径"""

    def test_returns_success_with_costs(self):
        db = MagicMock()
        project = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project

        mock_timesheets = [MagicMock(), MagicMock()]
        mock_user_costs = {
            1: {"total_hours": Decimal("8"), "items": []},
            2: {"total_hours": Decimal("4"), "items": []},
        }
        mock_created_costs = [MagicMock(), MagicMock()]
        mock_total_cost = Decimal("1200")

        import app.services.labor_cost.utils as utils_mod
        utils_mod.query_approved_timesheets = MagicMock(return_value=mock_timesheets)
        utils_mod.group_timesheets_by_user = MagicMock(return_value=mock_user_costs)
        utils_mod.process_user_costs = MagicMock(return_value=(mock_created_costs, mock_total_cost))
        utils_mod.delete_existing_costs = MagicMock()
        try:
            result = LaborCostService.calculate_project_labor_cost(db, project_id=1, recalculate=True)
        finally:
            # 不需要恢复，下个测试会重新import
            pass

        assert result["success"] is True
        assert result["cost_count"] == 2
        assert result["total_cost"] == float(mock_total_cost)
        assert result["user_count"] == 2


class TestCalculateAllProjectsLaborCost:
    """批量计算所有项目人工成本"""

    def test_empty_project_list_returns_success(self):
        db = MagicMock()
        # 没有任何工时项目
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        result = LaborCostService.calculate_all_projects_labor_cost(db)
        assert result["success"] is True
        assert result["total_projects"] == 0
        assert result["success_count"] == 0

    def test_counts_success_and_failure(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [(1,), (2,)]

        call_count = {"n": 0}

        def fake_calc(db, pid, *args, **kwargs):
            call_count["n"] += 1
            if pid == 1:
                return {"success": True}
            raise RuntimeError("计算失败")

        with patch.object(LaborCostService, "calculate_project_labor_cost", side_effect=fake_calc):
            result = LaborCostService.calculate_all_projects_labor_cost(db)

        assert result["success_count"] == 1
        assert result["fail_count"] == 1


class TestCalculateMonthlyLaborCost:
    """月度人工成本计算——验证正确传递日期范围"""

    def test_delegates_to_all_projects(self):
        db = MagicMock()
        with patch("app.services.labor_cost_service.get_month_range_by_ym",
                   return_value=(date(2025, 1, 1), date(2025, 1, 31))) as mock_range, \
             patch.object(LaborCostService, "calculate_all_projects_labor_cost",
                          return_value={"success": True}) as mock_all:
            result = LaborCostService.calculate_monthly_labor_cost(db, year=2025, month=1)

        mock_range.assert_called_once_with(2025, 1)
        mock_all.assert_called_once()
        assert result["success"] is True


class TestLaborCostServiceStaticHourlyRate:
    """get_user_hourly_rate 委托给 HourlyRateService"""

    def test_calls_hourly_rate_service(self):
        db = MagicMock()
        with patch("app.services.hourly_rate_service.HourlyRateService") as mock_cls:
            mock_cls.get_user_hourly_rate.return_value = Decimal("150")
            rate = LaborCostService.get_user_hourly_rate(db, user_id=5)
        mock_cls.get_user_hourly_rate.assert_called_once_with(db, 5, None)
        assert rate == Decimal("150")
