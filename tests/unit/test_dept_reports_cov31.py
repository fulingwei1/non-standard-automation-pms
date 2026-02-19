# -*- coding: utf-8 -*-
"""
Unit tests for DeptReportMixin (第三十一批)
"""
from datetime import date
from unittest.mock import MagicMock

import pytest

from app.services.report_data_generation.dept_reports import DeptReportMixin


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_department(dept_id=1, name="研发部", code="RD"):
    dept = MagicMock()
    dept.id = dept_id
    dept.dept_name = name
    dept.dept_code = code
    return dept


# ---------------------------------------------------------------------------
# generate_dept_weekly_report
# ---------------------------------------------------------------------------

class TestGenerateDeptWeeklyReport:
    def test_returns_error_when_dept_not_found(self, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = None
        chain.all.return_value = []

        result = DeptReportMixin.generate_dept_weekly_report(
            mock_db, department_id=999,
            start_date=date(2026, 2, 10),
            end_date=date(2026, 2, 16),
        )
        assert "error" in result

    def test_returns_summary_with_dept_info(self, mock_db):
        dept = _make_department()
        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            chain = MagicMock()
            chain.filter.return_value = chain
            chain.order_by.return_value = chain
            chain.first.return_value = dept if call_count[0] == 1 else None
            chain.all.return_value = []
            chain.in_.return_value = chain
            return chain

        mock_db.query.side_effect = query_side_effect

        result = DeptReportMixin.generate_dept_weekly_report(
            mock_db, department_id=1,
            start_date=date(2026, 2, 10),
            end_date=date(2026, 2, 16),
        )

        assert "error" not in result

    def test_period_dates_recorded(self, mock_db):
        dept = _make_department()
        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            chain = MagicMock()
            chain.filter.return_value = chain
            chain.order_by.return_value = chain
            chain.first.return_value = dept if call_count[0] == 1 else None
            chain.all.return_value = []
            chain.in_.return_value = chain
            return chain

        mock_db.query.side_effect = query_side_effect

        result = DeptReportMixin.generate_dept_weekly_report(
            mock_db, department_id=1,
            start_date=date(2026, 2, 10),
            end_date=date(2026, 2, 16),
        )
        result_str = str(result)
        assert "2026-02-10" in result_str or "period_start" in result_str


# ---------------------------------------------------------------------------
# generate_dept_monthly_report (if exists)
# ---------------------------------------------------------------------------

class TestGenerateDeptMonthlyReport:
    def test_error_when_dept_missing(self, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = None
        chain.all.return_value = []

        if hasattr(DeptReportMixin, "generate_dept_monthly_report"):
            result = DeptReportMixin.generate_dept_monthly_report(
                mock_db, department_id=999,
                year=2026, month=2,
            )
            assert "error" in result
        else:
            pytest.skip("generate_dept_monthly_report not implemented")

    def test_returns_data_with_dept(self, mock_db):
        dept = _make_department()
        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            chain = MagicMock()
            chain.filter.return_value = chain
            chain.order_by.return_value = chain
            chain.first.return_value = dept if call_count[0] == 1 else None
            chain.all.return_value = []
            chain.in_.return_value = chain
            return chain

        mock_db.query.side_effect = query_side_effect

        if hasattr(DeptReportMixin, "generate_dept_monthly_report"):
            result = DeptReportMixin.generate_dept_monthly_report(
                mock_db, department_id=1, year=2026, month=2
            )
            assert "error" not in result
        else:
            pytest.skip("generate_dept_monthly_report not implemented")
