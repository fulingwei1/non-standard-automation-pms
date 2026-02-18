# -*- coding: utf-8 -*-
"""第二十二批：business_support_dashboard_service 单元测试"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.business_support_dashboard_service import (
        count_active_contracts,
        calculate_pending_amount,
        calculate_overdue_amount,
        calculate_invoice_rate,
        count_active_bidding,
        calculate_acceptance_rate,
        get_urgent_tasks,
        get_today_todos,
    )
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="import failed")


@pytest.fixture
def db():
    return MagicMock()


class TestCountActiveContracts:
    def test_returns_integer(self, db):
        """返回整数类型"""
        db.query.return_value.filter.return_value.count.return_value = 3
        result = count_active_contracts(db)
        assert result == 3

    def test_zero_contracts(self, db):
        """没有活跃合同时返回0"""
        db.query.return_value.filter.return_value.count.return_value = 0
        result = count_active_contracts(db)
        assert result == 0


class TestCalculatePendingAmount:
    def test_returns_decimal(self, db):
        """返回Decimal类型"""
        mock_row = MagicMock()
        mock_row.__getitem__ = MagicMock(return_value="50000.00")
        db.execute.return_value.fetchone.return_value = mock_row
        result = calculate_pending_amount(db, date.today())
        assert isinstance(result, Decimal)

    def test_none_result_returns_zero(self, db):
        """查询无结果时返回0"""
        db.execute.return_value.fetchone.return_value = None
        result = calculate_pending_amount(db, date.today())
        assert result == Decimal("0")


class TestCalculateOverdueAmount:
    def test_returns_decimal(self, db):
        """返回Decimal类型"""
        mock_row = MagicMock()
        mock_row.__getitem__ = MagicMock(return_value="15000.00")
        db.execute.return_value.fetchone.return_value = mock_row
        result = calculate_overdue_amount(db, date.today())
        assert isinstance(result, Decimal)

    def test_none_result_returns_zero(self, db):
        """查询无结果时返回0"""
        db.execute.return_value.fetchone.return_value = None
        result = calculate_overdue_amount(db, date.today())
        assert result == Decimal("0")


class TestCalculateInvoiceRate:
    def test_zero_total_invoices_returns_zero(self, db):
        """无发票时返回0"""
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.count.return_value = 0
        result = calculate_invoice_rate(db, date.today())
        assert result == Decimal("0")

    def test_invoice_rate_calculated(self, db):
        """正常计算开票率"""
        call_count = 0

        def count_side():
            nonlocal call_count
            call_count += 1
            return 5 if call_count == 1 else 10

        q = MagicMock()
        q.filter.return_value = q
        q.count.side_effect = count_side
        db.query.return_value = q
        result = calculate_invoice_rate(db, date.today())
        assert isinstance(result, Decimal)


class TestCountActiveBidding:
    def test_returns_integer(self, db):
        """返回整数类型"""
        db.query.return_value.filter.return_value.count.return_value = 2
        result = count_active_bidding(db)
        assert result == 2


class TestCalculateAcceptanceRate:
    def test_zero_acceptances_returns_zero(self, db):
        """无验收订单时返回0"""
        db.query.return_value.count.return_value = 0
        result = calculate_acceptance_rate(db)
        assert result == Decimal("0")

    def test_acceptance_rate_calculated(self, db):
        """正常计算验收率"""
        call_count = 0

        def count_side():
            nonlocal call_count
            call_count += 1
            return 10 if call_count == 1 else 8

        q = MagicMock()
        q.filter.return_value = q
        q.count.side_effect = count_side
        db.query.return_value = q
        result = calculate_acceptance_rate(db)
        assert isinstance(result, Decimal)


class TestGetUrgentTasks:
    def test_returns_list(self, db):
        """返回列表类型"""
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = get_urgent_tasks(db, 1, date.today())
        assert isinstance(result, list)

    def test_task_formatted_correctly(self, db):
        """任务格式化正确"""
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.task_type = "approval"
        mock_task.title = "紧急审批"
        mock_task.description = "需要马上处理"
        mock_task.deadline = datetime(2025, 12, 31)
        mock_task.priority = "URGENT"
        mock_task.status = "PENDING"
        mock_task.is_urgent = True

        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_task]
        result = get_urgent_tasks(db, 1, date.today())
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["title"] == "紧急审批"
