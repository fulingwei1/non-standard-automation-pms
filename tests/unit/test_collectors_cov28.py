# -*- coding: utf-8 -*-
"""第二十八批 - collectors (KPI数据采集器) 单元测试"""

import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.strategy.kpi_collector.collectors")

# 采集器通过 @register_collector 装饰器注册，导入时即执行
import app.services.strategy.kpi_collector.collectors  # noqa: F401

from app.services.strategy.kpi_collector.collectors import (
    collect_project_metrics,
    collect_finance_metrics,
    collect_purchase_metrics,
    collect_hr_metrics,
)


# ─── collect_project_metrics ────────────────────────────────

class TestCollectProjectMetrics:

    def _make_db(self, count=0, projects=None):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.count.return_value = count
        q.all.return_value = projects or []
        q.with_entities.return_value.scalar.return_value = None
        return db

    def test_project_count_returns_decimal(self):
        db = self._make_db(count=5)
        result = collect_project_metrics(db, metric="PROJECT_COUNT")
        assert result == Decimal(5)

    def test_project_count_with_status_filter(self):
        db = self._make_db(count=3)
        result = collect_project_metrics(
            db, metric="PROJECT_COUNT", filters={"status": "IN_PROGRESS"}
        )
        assert result == Decimal(3)

    def test_project_completion_rate_zero_when_no_projects(self):
        db = self._make_db(count=0)
        result = collect_project_metrics(db, metric="PROJECT_COMPLETION_RATE")
        assert result == Decimal(0)

    def test_project_completion_rate_calculation(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        # total = 4, completed = 2
        q.count.side_effect = [4, 2]
        q.all.return_value = []

        result = collect_project_metrics(db, metric="PROJECT_COMPLETION_RATE")
        assert result == Decimal("50.0")

    def test_project_on_time_rate_with_completed_projects(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q

        on_time_project = MagicMock()
        on_time_project.actual_end_date = date(2024, 5, 1)
        on_time_project.planned_end_date = date(2024, 5, 15)

        late_project = MagicMock()
        late_project.actual_end_date = date(2024, 6, 1)
        late_project.planned_end_date = date(2024, 5, 15)

        q.all.return_value = [on_time_project, late_project]

        result = collect_project_metrics(db, metric="PROJECT_ON_TIME_RATE")
        assert result == Decimal("50.0")

    def test_project_health_rate_calculation(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        # total=10, healthy=8
        q.count.side_effect = [10, 8]

        result = collect_project_metrics(db, metric="PROJECT_HEALTH_RATE")
        assert result == Decimal("80.0")

    def test_project_total_value(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.with_entities.return_value.scalar.return_value = 1500000

        result = collect_project_metrics(db, metric="PROJECT_TOTAL_VALUE")
        assert result == Decimal("1500000")

    def test_unknown_metric_returns_none(self):
        db = self._make_db()
        result = collect_project_metrics(db, metric="UNKNOWN_METRIC")
        assert result is None


# ─── collect_finance_metrics ─────────────────────────────────

class TestCollectFinanceMetrics:

    def test_contract_total_amount(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.scalar.return_value = 5000000

        result = collect_finance_metrics(db, metric="CONTRACT_TOTAL_AMOUNT")
        assert result == Decimal("5000000")

    def test_contract_total_amount_returns_zero_when_none(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.scalar.return_value = None

        result = collect_finance_metrics(db, metric="CONTRACT_TOTAL_AMOUNT")
        assert result == Decimal("0")

    def test_receivable_overdue_count(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.scalar.return_value = 7

        result = collect_finance_metrics(db, metric="RECEIVABLE_OVERDUE_COUNT")
        assert result == Decimal(7)

    def test_project_profit_margin_no_project_id_returns_none(self):
        db = MagicMock()
        result = collect_finance_metrics(
            db, metric="PROJECT_PROFIT_MARGIN", filters={}
        )
        assert result is None

    def test_project_profit_margin_no_project_returns_none(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = collect_finance_metrics(
            db, metric="PROJECT_PROFIT_MARGIN", filters={"project_id": 99}
        )
        assert result is None

    def test_project_profit_margin_calculation(self):
        db = MagicMock()
        project = MagicMock()
        project.contract_amount = Decimal("1000000")
        db.query.return_value.filter.return_value.first.return_value = project
        # cost = 600000
        db.query.return_value.filter.return_value.scalar.return_value = 600000

        result = collect_finance_metrics(
            db, metric="PROJECT_PROFIT_MARGIN", filters={"project_id": 1}
        )
        # (1000000 - 600000) / 1000000 * 100 = 40%
        assert result == Decimal("40.0")

    def test_unknown_metric_returns_none(self):
        db = MagicMock()
        result = collect_finance_metrics(db, metric="NOT_EXIST")
        assert result is None


# ─── collect_purchase_metrics ────────────────────────────────

class TestCollectPurchaseMetrics:

    def test_po_count(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.count.return_value = 12

        result = collect_purchase_metrics(db, metric="PO_COUNT")
        assert result == Decimal(12)

    def test_po_total_amount(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.with_entities.return_value.scalar.return_value = 250000

        result = collect_purchase_metrics(db, metric="PO_TOTAL_AMOUNT")
        assert result == Decimal("250000")

    def test_po_on_time_rate_no_deliveries(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.all.return_value = []

        result = collect_purchase_metrics(db, metric="PO_ON_TIME_RATE")
        assert result == Decimal(0)

    def test_po_on_time_rate_with_deliveries(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q

        po_on_time = MagicMock()
        po_on_time.actual_delivery_date = date(2024, 3, 1)
        po_on_time.expected_delivery_date = date(2024, 3, 5)

        po_late = MagicMock()
        po_late.actual_delivery_date = date(2024, 3, 10)
        po_late.expected_delivery_date = date(2024, 3, 5)

        q.all.return_value = [po_on_time, po_late]

        result = collect_purchase_metrics(db, metric="PO_ON_TIME_RATE")
        assert result == Decimal("50.0")

    def test_unknown_metric_returns_none(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        result = collect_purchase_metrics(db, metric="UNKNOWN")
        assert result is None


# ─── collect_hr_metrics ──────────────────────────────────────

class TestCollectHrMetrics:

    def test_employee_count(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.scalar.return_value = 50

        result = collect_hr_metrics(db, metric="EMPLOYEE_COUNT")
        assert result == Decimal(50)

    def test_employee_active_count(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.scalar.return_value = 45

        result = collect_hr_metrics(db, metric="EMPLOYEE_ACTIVE_COUNT")
        assert result == Decimal(45)

    def test_employee_resigned_count(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.join.return_value.filter.return_value.scalar.return_value = 5
        q.scalar.return_value = 5

        result = collect_hr_metrics(db, metric="EMPLOYEE_RESIGNED_COUNT")
        assert result == Decimal(5)

    def test_employee_turnover_rate_zero_total(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.scalar.return_value = 0

        result = collect_hr_metrics(db, metric="EMPLOYEE_TURNOVER_RATE")
        assert result == Decimal(0)

    def test_employee_confirmation_rate_no_data(self):
        """没有试用期数据时应返回 100%"""
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.scalar.return_value = 0

        result = collect_hr_metrics(db, metric="EMPLOYEE_CONFIRMATION_RATE")
        assert result == Decimal(100)

    def test_employee_probation_count(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.scalar.return_value = 3

        result = collect_hr_metrics(db, metric="EMPLOYEE_PROBATION_COUNT")
        assert result == Decimal(3)

    def test_unknown_metric_returns_none(self):
        db = MagicMock()
        result = collect_hr_metrics(db, metric="NON_EXIST")
        assert result is None
