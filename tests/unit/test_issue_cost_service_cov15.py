# -*- coding: utf-8 -*-
"""第十五批: issue_cost_service 单元测试"""
import pytest

pytest.importorskip("app.services.issue_cost_service")

from unittest.mock import MagicMock, patch
from decimal import Decimal
from app.services.issue_cost_service import IssueCostService


def test_get_issue_related_costs_no_records():
    db = MagicMock()
    with patch("app.services.issue_cost_service.apply_keyword_filter") as mock_filter:
        mock_q = MagicMock()
        mock_q.all.return_value = []
        mock_filter.return_value = mock_q
        result = IssueCostService.get_issue_related_costs(db, "IS-001")
        assert result["inventory_loss"] == Decimal(0)
        assert result["total_cost"] == Decimal(0)
        assert result["costs"] == []


def test_get_issue_related_costs_with_inventory():
    db = MagicMock()
    cost1 = MagicMock()
    cost1.description = "IS-001 库存损耗"
    cost1.amount = Decimal("500")
    cost2 = MagicMock()
    cost2.description = "IS-001 人工费"
    cost2.amount = Decimal("200")
    with patch("app.services.issue_cost_service.apply_keyword_filter") as mock_filter:
        mock_q = MagicMock()
        mock_q.all.return_value = [cost1, cost2]
        mock_filter.return_value = mock_q
        result = IssueCostService.get_issue_related_costs(db, "IS-001")
        assert result["inventory_loss"] == Decimal("500")
        assert result["total_cost"] == Decimal("700")


def test_get_issue_related_hours_approved_only():
    db = MagicMock()
    ts1 = MagicMock()
    ts1.status = "APPROVED"
    ts1.hours = Decimal("8")
    ts2 = MagicMock()
    ts2.status = "PENDING"
    ts2.hours = Decimal("4")
    with patch("app.services.issue_cost_service.apply_keyword_filter") as mock_filter:
        mock_q = MagicMock()
        mock_q.all.return_value = [ts1, ts2]
        mock_filter.return_value = mock_q
        result = IssueCostService.get_issue_related_hours(db, "IS-001")
        assert result["total_hours"] == Decimal("8")
        assert len(result["timesheets"]) == 1


def test_get_issue_related_hours_no_timesheets():
    db = MagicMock()
    with patch("app.services.issue_cost_service.apply_keyword_filter") as mock_filter:
        mock_q = MagicMock()
        mock_q.all.return_value = []
        mock_filter.return_value = mock_q
        result = IssueCostService.get_issue_related_hours(db, "IS-002")
        assert result["total_hours"] == Decimal(0)
        assert result["timesheets"] == []


def test_get_issue_cost_summary():
    db = MagicMock()
    with patch.object(
        IssueCostService, "get_issue_related_costs",
        return_value={
            "inventory_loss": Decimal("300"),
            "total_cost": Decimal("800"),
            "costs": [MagicMock(), MagicMock()]
        }
    ), patch.object(
        IssueCostService, "get_issue_related_hours",
        return_value={
            "total_hours": Decimal("12"),
            "timesheets": [MagicMock()]
        }
    ):
        result = IssueCostService.get_issue_cost_summary(db, "IS-003")
        assert result["issue_no"] == "IS-003"
        assert result["inventory_loss"] == Decimal("300")
        assert result["total_cost"] == Decimal("800")
        assert result["total_hours"] == Decimal("12")
        assert result["cost_count"] == 2
        assert result["timesheet_count"] == 1


def test_get_issue_related_costs_none_amount():
    db = MagicMock()
    cost1 = MagicMock()
    cost1.description = "IS-004 库存"
    cost1.amount = None
    with patch("app.services.issue_cost_service.apply_keyword_filter") as mock_filter:
        mock_q = MagicMock()
        mock_q.all.return_value = [cost1]
        mock_filter.return_value = mock_q
        result = IssueCostService.get_issue_related_costs(db, "IS-004")
        assert result["inventory_loss"] == Decimal(0)
        assert result["total_cost"] == Decimal(0)
