# -*- coding: utf-8 -*-
"""Tests for app.services.strategy.kpi_collector.collectors"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


# We need to mock the registry decorator before importing
# The collectors are auto-registered on import via @register_collector


class TestCollectProjectMetrics:
    def _call(self, db, metric, filters=None, aggregation="COUNT"):
        from app.services.strategy.kpi_collector.collectors import collect_project_metrics
        return collect_project_metrics(db, metric, filters, aggregation)

    def test_project_count(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 10
        db.query.return_value = q

        result = self._call(db, "PROJECT_COUNT")
        assert result == Decimal(10)

    def test_project_completion_rate_zero_total(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 0
        db.query.return_value = q

        result = self._call(db, "PROJECT_COMPLETION_RATE")
        assert result == Decimal(0)

    def test_project_completion_rate(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.side_effect = [10, 3]  # total=10, completed=3
        db.query.return_value = q

        result = self._call(db, "PROJECT_COMPLETION_RATE")
        assert result == Decimal("30.0")

    def test_project_on_time_rate_no_completed(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = self._call(db, "PROJECT_ON_TIME_RATE")
        assert result == Decimal(0)

    def test_project_on_time_rate(self):
        from datetime import date
        db = MagicMock()
        p1 = MagicMock(actual_end_date=date(2025, 1, 10), planned_end_date=date(2025, 1, 15))
        p2 = MagicMock(actual_end_date=date(2025, 1, 20), planned_end_date=date(2025, 1, 15))

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [p1, p2]
        db.query.return_value = q

        result = self._call(db, "PROJECT_ON_TIME_RATE")
        assert result == Decimal("50.0")

    def test_project_health_rate(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.side_effect = [10, 8]
        db.query.return_value = q

        result = self._call(db, "PROJECT_HEALTH_RATE")
        assert result == Decimal("80.0")

    def test_project_total_value(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.with_entities.return_value = q
        q.scalar.return_value = 500000
        db.query.return_value = q

        result = self._call(db, "PROJECT_TOTAL_VALUE")
        assert result == Decimal("500000")

    def test_unknown_metric(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        db.query.return_value = q
        assert self._call(db, "UNKNOWN") is None

    def test_with_filters(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 5
        db.query.return_value = q

        result = self._call(db, "PROJECT_COUNT", filters={"status": "IN_PROGRESS", "year": 2025})
        assert result == Decimal(5)


class TestCollectFinanceMetrics:
    def _call(self, db, metric, filters=None, aggregation="SUM"):
        from app.services.strategy.kpi_collector.collectors import collect_finance_metrics
        return collect_finance_metrics(db, metric, filters, aggregation)

    def test_contract_total_amount(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.scalar.return_value = 1000000
        db.query.return_value = q

        result = self._call(db, "CONTRACT_TOTAL_AMOUNT")
        assert result == Decimal("1000000")

    def test_contract_total_amount_none(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.scalar.return_value = None
        db.query.return_value = q

        result = self._call(db, "CONTRACT_TOTAL_AMOUNT")
        assert result == Decimal("0")

    def test_contract_received_amount(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.scalar.return_value = 500000
        db.query.return_value = q

        result = self._call(db, "CONTRACT_RECEIVED_AMOUNT")
        assert result == Decimal("500000")

    def test_project_cost_total(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.scalar.return_value = 300000
        db.query.return_value = q

        result = self._call(db, "PROJECT_COST_TOTAL")
        assert result == Decimal("300000")

    def test_project_profit_margin_no_project_id(self):
        db = MagicMock()
        result = self._call(db, "PROJECT_PROFIT_MARGIN")
        assert result is None

    def test_project_profit_margin(self):
        db = MagicMock()
        project = MagicMock(contract_amount=1000000)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = project
        q.scalar.return_value = 600000  # cost
        db.query.return_value = q

        result = self._call(db, "PROJECT_PROFIT_MARGIN", filters={"project_id": 1})
        assert result == Decimal("40.0")

    def test_project_profit_margin_no_project(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q

        result = self._call(db, "PROJECT_PROFIT_MARGIN", filters={"project_id": 1})
        assert result is None

    def test_receivable_overdue_amount(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.scalar.return_value = 50000
        db.query.return_value = q

        result = self._call(db, "RECEIVABLE_OVERDUE_AMOUNT")
        assert result == Decimal("50000")

    def test_receivable_overdue_count(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.scalar.return_value = 3
        db.query.return_value = q

        result = self._call(db, "RECEIVABLE_OVERDUE_COUNT")
        assert result == Decimal(3)

    def test_unknown_metric(self):
        db = MagicMock()
        assert self._call(db, "UNKNOWN") is None


class TestCollectPurchaseMetrics:
    def _call(self, db, metric, filters=None, aggregation="SUM"):
        from app.services.strategy.kpi_collector.collectors import collect_purchase_metrics
        return collect_purchase_metrics(db, metric, filters, aggregation)

    def test_po_count(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 15
        db.query.return_value = q

        result = self._call(db, "PO_COUNT")
        assert result == Decimal(15)

    def test_po_total_amount(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.with_entities.return_value = q
        q.scalar.return_value = 200000
        db.query.return_value = q

        result = self._call(db, "PO_TOTAL_AMOUNT")
        assert result == Decimal("200000")

    def test_po_on_time_rate_no_delivered(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = self._call(db, "PO_ON_TIME_RATE")
        assert result == Decimal(0)

    def test_po_on_time_rate(self):
        from datetime import date
        db = MagicMock()
        po1 = MagicMock(actual_delivery_date=date(2025, 1, 10), expected_delivery_date=date(2025, 1, 15))
        po2 = MagicMock(actual_delivery_date=date(2025, 1, 20), expected_delivery_date=date(2025, 1, 15))

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [po1, po2]
        db.query.return_value = q

        result = self._call(db, "PO_ON_TIME_RATE")
        assert result == Decimal("50.0")

    def test_unknown_metric(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        db.query.return_value = q
        assert self._call(db, "UNKNOWN") is None


class TestCollectHRMetrics:
    def _call(self, db, metric, filters=None, aggregation="COUNT"):
        from app.services.strategy.kpi_collector.collectors import collect_hr_metrics
        return collect_hr_metrics(db, metric, filters, aggregation)

    def test_employee_count(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        q.scalar.return_value = 50
        db.query.return_value = q

        result = self._call(db, "EMPLOYEE_COUNT")
        assert result == Decimal(50)

    def test_employee_active_count(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        q.scalar.return_value = 45
        db.query.return_value = q

        result = self._call(db, "EMPLOYEE_ACTIVE_COUNT")
        assert result == Decimal(45)

    def test_employee_resigned_count(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        q.scalar.return_value = 5
        db.query.return_value = q

        result = self._call(db, "EMPLOYEE_RESIGNED_COUNT")
        assert result == Decimal(5)

    def test_employee_turnover_rate_zero_total(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        q.scalar.return_value = 0
        db.query.return_value = q

        result = self._call(db, "EMPLOYEE_TURNOVER_RATE")
        assert result == Decimal(0)

    def test_employee_turnover_rate(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        q.scalar.side_effect = [100, 10]
        db.query.return_value = q

        result = self._call(db, "EMPLOYEE_TURNOVER_RATE")
        assert result == Decimal("10.0")

    def test_employee_probation_count(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.scalar.return_value = 3
        db.query.return_value = q

        result = self._call(db, "EMPLOYEE_PROBATION_COUNT")
        assert result == Decimal(3)

    def test_employee_confirmation_rate_no_data(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.scalar.side_effect = [0, 0]
        db.query.return_value = q

        result = self._call(db, "EMPLOYEE_CONFIRMATION_RATE")
        assert result == Decimal(100)

    def test_employee_confirmation_rate(self):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.scalar.side_effect = [8, 2]  # confirmed=8, probation_resigned=2
        db.query.return_value = q

        result = self._call(db, "EMPLOYEE_CONFIRMATION_RATE")
        assert result == Decimal("80.0")

    def test_unknown_metric(self):
        db = MagicMock()
        assert self._call(db, "UNKNOWN") is None
