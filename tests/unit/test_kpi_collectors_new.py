# -*- coding: utf-8 -*-
"""
KPI采集器单元测试 (F组) - 使用MagicMock方式

测试覆盖：
- collect_project_metrics: 项目指标采集
- collect_finance_metrics: 财务指标采集
- collect_purchase_metrics: 采购指标采集
- collect_hr_metrics: HR指标采集
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.strategy.kpi_collector.collectors import (
    collect_project_metrics,
    collect_finance_metrics,
    collect_purchase_metrics,
    collect_hr_metrics,
)


@pytest.fixture
def db():
    return MagicMock()


# ============================================================
# collect_project_metrics 测试
# ============================================================

class TestCollectProjectMetrics:

    def test_project_count(self, db):
        """测试项目数量采集"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.count.return_value = 10
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Project'):
            result = collect_project_metrics(db, "PROJECT_COUNT")
        assert result == Decimal("10")

    def test_project_completion_rate_no_projects(self, db):
        """测试无项目时完成率为0"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.count.return_value = 0
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Project'):
            result = collect_project_metrics(db, "PROJECT_COMPLETION_RATE")
        assert result == Decimal("0")

    def test_project_completion_rate_with_projects(self, db):
        """测试有项目时完成率计算"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        # total=10, completed=5 -> 50%
        mock_q.count.side_effect = [10, 5]
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Project'):
            result = collect_project_metrics(db, "PROJECT_COMPLETION_RATE")
        assert result == Decimal("50.0")

    def test_project_on_time_rate_no_completed(self, db):
        """测试无完成项目时准时率为0"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Project'):
            result = collect_project_metrics(db, "PROJECT_ON_TIME_RATE")
        assert result == Decimal("0")

    def test_project_on_time_rate_all_on_time(self, db):
        """测试全部准时完成"""
        from datetime import date
        p1 = MagicMock(actual_end_date=date(2025, 1, 10), planned_end_date=date(2025, 1, 15))
        p2 = MagicMock(actual_end_date=date(2025, 1, 20), planned_end_date=date(2025, 1, 25))
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [p1, p2]
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Project'):
            result = collect_project_metrics(db, "PROJECT_ON_TIME_RATE")
        assert result == Decimal("100.0")

    def test_project_health_rate(self, db):
        """测试项目健康率"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.count.side_effect = [20, 15]  # total=20, H1=15 -> 75%
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Project'):
            result = collect_project_metrics(db, "PROJECT_HEALTH_RATE")
        assert result == Decimal("75.0")

    def test_project_total_value(self, db):
        """测试项目总金额"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.with_entities.return_value.scalar.return_value = 500000
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Project'):
            result = collect_project_metrics(db, "PROJECT_TOTAL_VALUE")
        assert result == Decimal("500000")

    def test_project_total_value_none(self, db):
        """测试无合同金额时返回0"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.with_entities.return_value.scalar.return_value = None
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Project'):
            result = collect_project_metrics(db, "PROJECT_TOTAL_VALUE")
        assert result == Decimal("0")

    def test_unknown_metric_returns_none(self, db):
        """测试未知指标返回None"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Project'):
            result = collect_project_metrics(db, "UNKNOWN_METRIC")
        assert result is None

    def test_with_status_filter(self, db):
        """测试应用状态筛选"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.count.return_value = 5
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Project'):
            result = collect_project_metrics(db, "PROJECT_COUNT", filters={"status": "COMPLETED"})
        assert result == Decimal("5")


# ============================================================
# collect_finance_metrics 测试
# ============================================================

class TestCollectFinanceMetrics:

    def test_contract_total_amount(self, db):
        """测试合同总金额"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.scalar.return_value = 1000000
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Contract', MagicMock()):
            with patch('app.services.strategy.kpi_collector.collectors.ProjectCost', MagicMock(), create=True):
                with patch('app.services.strategy.kpi_collector.collectors.ProjectPaymentPlan', MagicMock(), create=True):
                    result = collect_finance_metrics(db, "CONTRACT_TOTAL_AMOUNT")
        assert result == Decimal("1000000")

    def test_contract_total_amount_null(self, db):
        """测试合同总金额为空时返回0"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.scalar.return_value = None
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Contract', MagicMock()):
            result = collect_finance_metrics(db, "CONTRACT_TOTAL_AMOUNT")
        assert result == Decimal("0")

    def test_unknown_finance_metric(self, db):
        """测试未知财务指标"""
        result = collect_finance_metrics(db, "UNKNOWN_METRIC")
        assert result is None

    def test_receivable_overdue_count(self, db):
        """测试逾期应收款笔数"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.scalar.return_value = 3
        db.query.return_value = mock_q

        result = collect_finance_metrics(db, "RECEIVABLE_OVERDUE_COUNT")
        assert result == Decimal("3")


# ============================================================
# collect_purchase_metrics 测试
# ============================================================

class TestCollectPurchaseMetrics:

    def test_po_count(self, db):
        """测试采购订单数量"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.count.return_value = 25
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.PurchaseOrder', MagicMock(), create=True):
            result = collect_purchase_metrics(db, "PO_COUNT")
        assert result == Decimal("25")

    def test_po_total_amount(self, db):
        """测试采购总金额"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.with_entities.return_value.scalar.return_value = 250000
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.PurchaseOrder', MagicMock(), create=True):
            result = collect_purchase_metrics(db, "PO_TOTAL_AMOUNT")
        assert result == Decimal("250000")

    def test_po_on_time_rate_no_deliveries(self, db):
        """测试无到货时准时率为0"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.PurchaseOrder', MagicMock(), create=True):
            result = collect_purchase_metrics(db, "PO_ON_TIME_RATE")
        assert result == Decimal("0")

    def test_po_on_time_rate_with_data(self, db):
        """测试准时到货率计算"""
        from datetime import date
        po1 = MagicMock(actual_delivery_date=date(2025, 1, 10), expected_delivery_date=date(2025, 1, 12))
        po2 = MagicMock(actual_delivery_date=date(2025, 1, 20), expected_delivery_date=date(2025, 1, 15))
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [po1, po2]
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.PurchaseOrder', MagicMock(), create=True):
            result = collect_purchase_metrics(db, "PO_ON_TIME_RATE")
        assert result == Decimal("50.0")

    def test_unknown_purchase_metric(self, db):
        """测试未知采购指标"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.PurchaseOrder', MagicMock(), create=True):
            result = collect_purchase_metrics(db, "UNKNOWN")
        assert result is None


# ============================================================
# collect_hr_metrics 测试
# ============================================================

class TestCollectHrMetrics:

    def test_employee_count(self, db):
        """测试员工总数"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.scalar.return_value = 50
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Employee', MagicMock(), create=True):
            result = collect_hr_metrics(db, "EMPLOYEE_COUNT")
        assert result == Decimal("50")

    def test_employee_active_count(self, db):
        """测试在职员工数"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.scalar.return_value = 45
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Employee', MagicMock(), create=True):
            result = collect_hr_metrics(db, "EMPLOYEE_ACTIVE_COUNT")
        assert result == Decimal("45")

    def test_employee_resigned_count(self, db):
        """测试离职员工数"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.scalar.return_value = 5
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Employee', MagicMock(), create=True):
            with patch('app.services.strategy.kpi_collector.collectors.EmployeeHrProfile', MagicMock(), create=True):
                result = collect_hr_metrics(db, "EMPLOYEE_RESIGNED_COUNT")
        assert result == Decimal("5")

    def test_employee_turnover_rate_zero_total(self, db):
        """测试总人数为0时离职率为0"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.scalar.side_effect = [0]  # total = 0
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Employee', MagicMock(), create=True):
            result = collect_hr_metrics(db, "EMPLOYEE_TURNOVER_RATE")
        assert result == Decimal("0")

    def test_employee_probation_count(self, db):
        """测试试用期员工数"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.scalar.return_value = 8
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Employee', MagicMock(), create=True):
            result = collect_hr_metrics(db, "EMPLOYEE_PROBATION_COUNT")
        assert result == Decimal("8")

    def test_employee_confirmation_rate_no_data(self, db):
        """测试无试用期数据时转正率默认100%"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.scalar.side_effect = [0, 0]  # confirmed=0, probation_resigned=0
        db.query.return_value = mock_q

        with patch('app.services.strategy.kpi_collector.collectors.Employee', MagicMock(), create=True):
            with patch('app.services.strategy.kpi_collector.collectors.EmployeeHrProfile', MagicMock(), create=True):
                result = collect_hr_metrics(db, "EMPLOYEE_CONFIRMATION_RATE")
        assert result == Decimal("100")

    def test_unknown_hr_metric(self, db):
        """测试未知HR指标"""
        result = collect_hr_metrics(db, "UNKNOWN_HR_METRIC")
        assert result is None
