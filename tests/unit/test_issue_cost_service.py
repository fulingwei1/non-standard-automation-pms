# -*- coding: utf-8 -*-
"""
问题成本关联服务测试
"""

from decimal import Decimal

from unittest.mock import MagicMock

from app.models.project import ProjectCost
from app.models.timesheet import Timesheet
from app.services.issue_cost_service import IssueCostService


class TestGetIssueRelatedCosts:
    """测试获取问题关联成本"""

    def test_empty_query_returns_empty_costs(self, db_session):
        """空查询返回空成本记录"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = IssueCostService.get_issue_related_costs(mock_session, "ISSUE-001")

        assert result["inventory_loss"] == Decimal(0)
        assert result["total_cost"] == Decimal(0)
        assert result["costs"] == []

    def test_single_cost_record(self, db_session):
        """单个成本记录"""
        mock_cost = MagicMock(spec=ProjectCost)
        mock_cost.amount = Decimal("1000.00")
        mock_cost.description = "材料成本 - ISSUE-001"

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_cost
        ]

        result = IssueCostService.get_issue_related_costs(mock_session, "ISSUE-001")

        assert result["total_cost"] == Decimal("1000.00")
        assert len(result["costs"]) == 1

    def test_multiple_cost_records(self, db_session):
        """多个成本记录"""
        mock_cost1 = MagicMock(spec=ProjectCost)
        mock_cost1.amount = Decimal("500.00")
        mock_cost1.description = "人工成本 ISSUE-001"

        mock_cost2 = MagicMock(spec=ProjectCost)
        mock_cost2.amount = Decimal("300.00")
        mock_cost2.description = "设备成本 ISSUE-001"

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_cost1,
            mock_cost2,
        ]

        result = IssueCostService.get_issue_related_costs(mock_session, "ISSUE-001")

        assert result["total_cost"] == Decimal("800.00")
        assert len(result["costs"]) == 2

    def test_calculates_inventory_loss(self, db_session):
        """计算库存损失"""
        mock_cost1 = MagicMock(spec=ProjectCost)
        mock_cost1.amount = Decimal("200.00")
        mock_cost1.description = "库存损失 - ISSUE-001"

        mock_cost2 = MagicMock(spec=ProjectCost)
        mock_cost2.amount = Decimal("300.00")
        mock_cost2.description = "人工成本 ISSUE-001"

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_cost1,
            mock_cost2,
        ]

        result = IssueCostService.get_issue_related_costs(mock_session, "ISSUE-001")

        assert result["inventory_loss"] == Decimal("200.00")
        assert result["total_cost"] == Decimal("500.00")

    def test_zero_amount_costs(self, db_session):
        """零金额成本"""
        mock_cost1 = MagicMock(spec=ProjectCost)
        mock_cost1.amount = None
        mock_cost1.description = "ISSUE-001"

        mock_cost2 = MagicMock(spec=ProjectCost)
        mock_cost2.amount = Decimal(0)
        mock_cost2.description = "ISSUE-001"

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_cost1,
            mock_cost2,
        ]

        result = IssueCostService.get_issue_related_costs(mock_session, "ISSUE-001")

        assert result["total_cost"] == Decimal(0)
        assert result["inventory_loss"] == Decimal(0)


class TestGetIssueRelatedHours:
    """测试获取问题关联工时"""

    def test_empty_query_returns_zero_hours(self, db_session):
        """空查询返回零工时"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = IssueCostService.get_issue_related_hours(mock_session, "ISSUE-001")

        assert result["total_hours"] == Decimal(0)
        assert result["timesheets"] == []

    def test_single_timesheet(self, db_session):
        """单个工时记录"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.hours = Decimal("8.00")
        mock_timesheet.status = "APPROVED"
        mock_timesheet.work_content = "解决 ISSUE-001"

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_timesheet
        ]

        result = IssueCostService.get_issue_related_hours(mock_session, "ISSUE-001")

        assert result["total_hours"] == Decimal("8.00")
        assert len(result["timesheets"]) == 1

    def test_multiple_timesheets(self, db_session):
        """多个工时记录"""
        mock_timesheet1 = MagicMock(spec=Timesheet)
        mock_timesheet1.hours = Decimal("4.00")
        mock_timesheet1.status = "APPROVED"
        mock_timesheet1.work_content = "ISSUE-001"

        mock_timesheet2 = MagicMock(spec=Timesheet)
        mock_timesheet2.hours = Decimal("6.00")
        mock_timesheet2.status = "APPROVED"
        mock_timesheet2.work_result = "完成 ISSUE-001"

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_timesheet1,
            mock_timesheet2,
        ]

        result = IssueCostService.get_issue_related_hours(mock_session, "ISSUE-001")

        assert result["total_hours"] == Decimal("10.00")
        assert len(result["timesheets"]) == 2

    def test_filters_by_status_approved(self, db_session):
        """只统计已审批的工时"""
        mock_timesheet1 = MagicMock(spec=Timesheet)
        mock_timesheet1.hours = Decimal("8.00")
        mock_timesheet1.status = "APPROVED"
        mock_timesheet1.work_content = "ISSUE-001"

        mock_timesheet2 = MagicMock(spec=Timesheet)
        mock_timesheet2.hours = Decimal("4.00")
        mock_timesheet2.status = "PENDING"
        mock_timesheet2.work_content = "ISSUE-001"

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_timesheet1,
            mock_timesheet2,
        ]

        result = IssueCostService.get_issue_related_hours(mock_session, "ISSUE-001")

        assert result["total_hours"] == Decimal("8.00")
        assert len(result["timesheets"]) == 1

    def test_zero_hours_timesheets(self, db_session):
        """零工时记录"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.hours = None
        mock_timesheet.status = "APPROVED"
        mock_timesheet.work_content = "ISSUE-001"

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_timesheet
        ]

        result = IssueCostService.get_issue_related_hours(mock_session, "ISSUE-001")

        assert result["total_hours"] == Decimal(0)


class TestGetIssueCostSummary:
    """测试获取问题成本汇总"""

    def test_combined_costs_and_hours(self, db_session):
        """合并成本和工时"""
        mock_session = MagicMock()

        mock_cost = MagicMock(spec=ProjectCost)
        mock_cost.amount = Decimal("500.00")
        mock_cost.description = "ISSUE-001"

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.hours = Decimal("8.00")
        mock_timesheet.status = "APPROVED"
        mock_timesheet.work_content = "ISSUE-001"

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_cost
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_timesheet
        ]

        result = IssueCostService.get_issue_cost_summary(mock_session, "ISSUE-001")

        assert result["issue_no"] == "ISSUE-001"
        assert result["total_cost"] == Decimal("500.00")
        assert result["total_hours"] == Decimal("8.00")
        assert result["cost_count"] == 1
        assert result["timesheet_count"] == 1

    def test_empty_summary(self, db_session):
        """空汇总"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = IssueCostService.get_issue_cost_summary(mock_session, "ISSUE-001")

        assert result["issue_no"] == "ISSUE-001"
        assert result["inventory_loss"] == Decimal(0)
        assert result["total_cost"] == Decimal(0)
        assert result["total_hours"] == Decimal(0)
        assert result["cost_count"] == 0
        assert result["timesheet_count"] == 0
