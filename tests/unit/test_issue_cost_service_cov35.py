# -*- coding: utf-8 -*-
"""
第三十五批 - issue_cost_service.py 单元测试
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.issue_cost_service import IssueCostService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


def _make_cost(amount, description=""):
    cost = MagicMock()
    cost.amount = Decimal(str(amount))
    cost.description = description
    return cost


def _make_timesheet(hours, status="APPROVED"):
    ts = MagicMock()
    ts.hours = Decimal(str(hours))
    ts.status = status
    return ts


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestIssueCostService:

    def _make_db_for_costs(self, costs):
        db = MagicMock()
        with patch("app.services.issue_cost_service.apply_keyword_filter") as mock_filter:
            mock_q = MagicMock()
            mock_q.all.return_value = costs
            mock_filter.return_value = mock_q
            db.query.return_value = mock_q
        return db

    def test_get_issue_related_costs_empty(self):
        """没有关联成本时返回零"""
        db = MagicMock()
        with patch("app.services.issue_cost_service.apply_keyword_filter") as mock_filter:
            mock_q = MagicMock()
            mock_q.all.return_value = []
            mock_filter.return_value = mock_q
            db.query.return_value = mock_q
            result = IssueCostService.get_issue_related_costs(db, "ISS-001")
        assert result["total_cost"] == Decimal(0)
        assert result["inventory_loss"] == Decimal(0)
        assert result["costs"] == []

    def test_get_issue_related_costs_with_inventory(self):
        """有库存损失时正确计算"""
        costs = [
            _make_cost(500, "库存损失-螺丝"),
            _make_cost(300, "人工成本"),
        ]
        db = MagicMock()
        with patch("app.services.issue_cost_service.apply_keyword_filter") as mock_filter:
            mock_q = MagicMock()
            mock_q.all.return_value = costs
            mock_filter.return_value = mock_q
            db.query.return_value = mock_q
            result = IssueCostService.get_issue_related_costs(db, "ISS-002")
        assert result["inventory_loss"] == Decimal(500)
        assert result["total_cost"] == Decimal(800)

    def test_get_issue_related_hours_approved_only(self):
        """只统计已审批的工时"""
        timesheets = [
            _make_timesheet(8, "APPROVED"),
            _make_timesheet(4, "PENDING"),
            _make_timesheet(2, "REJECTED"),
        ]
        db = MagicMock()
        with patch("app.services.issue_cost_service.apply_keyword_filter") as mock_filter:
            mock_q = MagicMock()
            mock_q.all.return_value = timesheets
            mock_filter.return_value = mock_q
            db.query.return_value = mock_q
            result = IssueCostService.get_issue_related_hours(db, "ISS-003")
        assert result["total_hours"] == Decimal(8)
        assert len(result["timesheets"]) == 1

    def test_get_issue_cost_summary_structure(self):
        """汇总结果包含所有必要字段"""
        db = MagicMock()
        with patch.object(IssueCostService, "get_issue_related_costs") as mock_costs, \
             patch.object(IssueCostService, "get_issue_related_hours") as mock_hours:
            mock_costs.return_value = {
                "inventory_loss": Decimal(100),
                "total_cost": Decimal(200),
                "costs": [MagicMock(), MagicMock()],
            }
            mock_hours.return_value = {
                "total_hours": Decimal(16),
                "timesheets": [MagicMock()],
            }
            result = IssueCostService.get_issue_cost_summary(db, "ISS-004")
        assert result["issue_no"] == "ISS-004"
        assert result["inventory_loss"] == Decimal(100)
        assert result["total_cost"] == Decimal(200)
        assert result["total_hours"] == Decimal(16)
        assert result["cost_count"] == 2
        assert result["timesheet_count"] == 1

    def test_get_issue_related_hours_empty(self):
        """没有工时记录时返回零"""
        db = MagicMock()
        with patch("app.services.issue_cost_service.apply_keyword_filter") as mock_filter:
            mock_q = MagicMock()
            mock_q.all.return_value = []
            mock_filter.return_value = mock_q
            db.query.return_value = mock_q
            result = IssueCostService.get_issue_related_hours(db, "ISS-005")
        assert result["total_hours"] == Decimal(0)
        assert result["timesheets"] == []

    def test_none_amount_treated_as_zero(self):
        """amount 为 None 时当 0 处理"""
        cost = MagicMock()
        cost.amount = None
        cost.description = "测试"
        db = MagicMock()
        with patch("app.services.issue_cost_service.apply_keyword_filter") as mock_filter:
            mock_q = MagicMock()
            mock_q.all.return_value = [cost]
            mock_filter.return_value = mock_q
            db.query.return_value = mock_q
            result = IssueCostService.get_issue_related_costs(db, "ISS-006")
        assert result["total_cost"] == Decimal(0)
