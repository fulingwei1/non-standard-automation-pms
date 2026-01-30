# -*- coding: utf-8 -*-
"""
IssueCostService 综合单元测试

测试覆盖:
- get_issue_related_costs: 获取问题关联的成本记录
- get_issue_related_hours: 获取问题关联的工时记录
- get_issue_cost_summary: 获取问题成本汇总
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestGetIssueRelatedCosts:
    """测试 get_issue_related_costs 方法"""

    def test_returns_empty_when_no_costs(self):
        """测试无成本记录时返回空"""
        from app.services.issue_cost_service import IssueCostService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = IssueCostService.get_issue_related_costs(mock_db, "ISS001")

        assert result['inventory_loss'] == Decimal(0)
        assert result['total_cost'] == Decimal(0)
        assert result['costs'] == []

    def test_returns_costs_matching_issue_no(self):
        """测试返回匹配问题编号的成本"""
        from app.services.issue_cost_service import IssueCostService

        mock_db = MagicMock()

        mock_cost1 = MagicMock()
        mock_cost1.description = "ISS001相关的成本"
        mock_cost1.amount = Decimal("1000")

        mock_cost2 = MagicMock()
        mock_cost2.description = "ISS001修复费用"
        mock_cost2.amount = Decimal("500")

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_cost1, mock_cost2]

        result = IssueCostService.get_issue_related_costs(mock_db, "ISS001")

        assert result['total_cost'] == Decimal("1500")
        assert len(result['costs']) == 2

    def test_calculates_inventory_loss(self):
        """测试计算库存损失"""
        from app.services.issue_cost_service import IssueCostService

        mock_db = MagicMock()

        mock_cost1 = MagicMock()
        mock_cost1.description = "ISS001库存损失"
        mock_cost1.amount = Decimal("2000")

        mock_cost2 = MagicMock()
        mock_cost2.description = "ISS001修复费用"
        mock_cost2.amount = Decimal("500")

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_cost1, mock_cost2]

        result = IssueCostService.get_issue_related_costs(mock_db, "ISS001")

        assert result['inventory_loss'] == Decimal("2000")
        assert result['total_cost'] == Decimal("2500")

    def test_handles_none_amount(self):
        """测试处理金额为None的成本"""
        from app.services.issue_cost_service import IssueCostService

        mock_db = MagicMock()

        mock_cost = MagicMock()
        mock_cost.description = "ISS001成本"
        mock_cost.amount = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_cost]

        result = IssueCostService.get_issue_related_costs(mock_db, "ISS001")

        assert result['total_cost'] == Decimal(0)

    def test_handles_none_description(self):
        """测试处理描述为None的成本"""
        from app.services.issue_cost_service import IssueCostService

        mock_db = MagicMock()

        mock_cost = MagicMock()
        mock_cost.description = None
        mock_cost.amount = Decimal("1000")

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_cost]

        result = IssueCostService.get_issue_related_costs(mock_db, "ISS001")

        assert result['inventory_loss'] == Decimal(0)
        assert result['total_cost'] == Decimal("1000")


class TestGetIssueRelatedHours:
    """测试 get_issue_related_hours 方法"""

    def test_returns_empty_when_no_timesheets(self):
        """测试无工时记录时返回空"""
        from app.services.issue_cost_service import IssueCostService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = IssueCostService.get_issue_related_hours(mock_db, "ISS001")

        assert result['total_hours'] == Decimal(0)
        assert result['timesheets'] == []

    def test_returns_only_approved_timesheets(self):
        """测试只返回已审批的工时"""
        from app.services.issue_cost_service import IssueCostService

        mock_db = MagicMock()

        mock_ts1 = MagicMock()
        mock_ts1.work_content = "处理ISS001问题"
        mock_ts1.work_result = "完成"
        mock_ts1.hours = Decimal("4")
        mock_ts1.status = "APPROVED"

        mock_ts2 = MagicMock()
        mock_ts2.work_content = "处理ISS001问题"
        mock_ts2.work_result = "进行中"
        mock_ts2.hours = Decimal("2")
        mock_ts2.status = "PENDING"  # 未审批

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ts1, mock_ts2]

        result = IssueCostService.get_issue_related_hours(mock_db, "ISS001")

        assert result['total_hours'] == Decimal("4")
        assert len(result['timesheets']) == 1

    def test_calculates_total_hours(self):
        """测试计算总工时"""
        from app.services.issue_cost_service import IssueCostService

        mock_db = MagicMock()

        mock_ts1 = MagicMock()
        mock_ts1.work_content = "处理ISS001"
        mock_ts1.hours = Decimal("4")
        mock_ts1.status = "APPROVED"

        mock_ts2 = MagicMock()
        mock_ts2.work_content = "继续处理ISS001"
        mock_ts2.hours = Decimal("6")
        mock_ts2.status = "APPROVED"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ts1, mock_ts2]

        result = IssueCostService.get_issue_related_hours(mock_db, "ISS001")

        assert result['total_hours'] == Decimal("10")
        assert len(result['timesheets']) == 2

    def test_handles_none_hours(self):
        """测试处理工时为None"""
        from app.services.issue_cost_service import IssueCostService

        mock_db = MagicMock()

        mock_ts = MagicMock()
        mock_ts.work_content = "处理ISS001"
        mock_ts.hours = None
        mock_ts.status = "APPROVED"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ts]

        result = IssueCostService.get_issue_related_hours(mock_db, "ISS001")

        assert result['total_hours'] == Decimal(0)

    def test_searches_in_work_content_and_result(self):
        """测试同时搜索work_content和work_result"""
        from app.services.issue_cost_service import IssueCostService

        mock_db = MagicMock()

        mock_ts1 = MagicMock()
        mock_ts1.work_content = "处理ISS001"
        mock_ts1.work_result = None
        mock_ts1.hours = Decimal("4")
        mock_ts1.status = "APPROVED"

        mock_ts2 = MagicMock()
        mock_ts2.work_content = "其他工作"
        mock_ts2.work_result = "解决了ISS001"
        mock_ts2.hours = Decimal("2")
        mock_ts2.status = "APPROVED"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ts1, mock_ts2]

        result = IssueCostService.get_issue_related_hours(mock_db, "ISS001")

        assert result['total_hours'] == Decimal("6")


class TestGetIssueCostSummary:
    """测试 get_issue_cost_summary 方法"""

    def test_returns_complete_summary(self):
        """测试返回完整汇总"""
        from app.services.issue_cost_service import IssueCostService

        mock_db = MagicMock()

        # Mock costs
        mock_cost = MagicMock()
        mock_cost.description = "ISS001库存损失"
        mock_cost.amount = Decimal("1000")

        # Mock timesheets
        mock_ts = MagicMock()
        mock_ts.work_content = "处理ISS001"
        mock_ts.hours = Decimal("5")
        mock_ts.status = "APPROVED"

        # Setup query chain for costs and timesheets
        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                result.all.return_value = [mock_cost]
            else:
                result.all.return_value = [mock_ts]
            return result

        mock_db.query.return_value.filter = filter_side_effect

        result = IssueCostService.get_issue_cost_summary(mock_db, "ISS001")

        assert result['issue_no'] == "ISS001"
        assert result['inventory_loss'] == Decimal("1000")
        assert result['total_cost'] == Decimal("1000")
        assert result['total_hours'] == Decimal("5")
        assert result['cost_count'] == 1
        assert result['timesheet_count'] == 1

    def test_returns_zero_for_no_data(self):
        """测试无数据时返回零"""
        from app.services.issue_cost_service import IssueCostService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = IssueCostService.get_issue_cost_summary(mock_db, "ISS999")

        assert result['issue_no'] == "ISS999"
        assert result['inventory_loss'] == Decimal(0)
        assert result['total_cost'] == Decimal(0)
        assert result['total_hours'] == Decimal(0)
        assert result['cost_count'] == 0
        assert result['timesheet_count'] == 0

    def test_handles_mixed_data(self):
        """测试处理混合数据"""
        from app.services.issue_cost_service import IssueCostService

        mock_db = MagicMock()

        # Multiple costs
        mock_cost1 = MagicMock()
        mock_cost1.description = "ISS001材料费"
        mock_cost1.amount = Decimal("500")

        mock_cost2 = MagicMock()
        mock_cost2.description = "ISS001库存损失"
        mock_cost2.amount = Decimal("1500")

        # Multiple timesheets
        mock_ts1 = MagicMock()
        mock_ts1.work_content = "处理ISS001"
        mock_ts1.hours = Decimal("3")
        mock_ts1.status = "APPROVED"

        mock_ts2 = MagicMock()
        mock_ts2.work_content = "ISS001修复"
        mock_ts2.hours = Decimal("4")
        mock_ts2.status = "APPROVED"

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                result.all.return_value = [mock_cost1, mock_cost2]
            else:
                result.all.return_value = [mock_ts1, mock_ts2]
            return result

        mock_db.query.return_value.filter = filter_side_effect

        result = IssueCostService.get_issue_cost_summary(mock_db, "ISS001")

        assert result['inventory_loss'] == Decimal("1500")
        assert result['total_cost'] == Decimal("2000")
        assert result['total_hours'] == Decimal("7")
        assert result['cost_count'] == 2
        assert result['timesheet_count'] == 2
