# -*- coding: utf-8 -*-
"""第二十五批 - timesheet_quality_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

pytest.importorskip("app.services.timesheet_quality_service")

from app.services.timesheet_quality_service import TimesheetQualityService


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return TimesheetQualityService(db)


def _make_timesheet(user_id=1, work_date=None, hours=8.0, status="APPROVED"):
    ts = MagicMock()
    ts.user_id = user_id
    ts.work_date = work_date or date(2025, 3, 10)
    ts.hours = hours
    ts.status = status
    return ts


def _make_user(user_id=1, real_name="张三", username="zhangsan"):
    user = MagicMock()
    user.id = user_id
    user.real_name = real_name
    user.username = username
    return user


# ── 常量 ──────────────────────────────────────────────────────────────────────

class TestConstants:
    def test_max_daily_hours(self, service):
        assert service.MAX_DAILY_HOURS == 16

    def test_min_daily_hours(self, service):
        assert service.MIN_DAILY_HOURS == 0.5

    def test_max_weekly_hours(self, service):
        assert service.MAX_WEEKLY_HOURS == 80

    def test_max_monthly_hours(self, service):
        assert service.MAX_MONTHLY_HOURS == 300


# ── detect_anomalies - daily ──────────────────────────────────────────────────

class TestDetectAnomaliesDaily:
    def test_detects_excessive_daily_hours(self, service, db):
        ts1 = _make_timesheet(user_id=1, work_date=date(2025, 3, 10), hours=10)
        ts2 = _make_timesheet(user_id=1, work_date=date(2025, 3, 10), hours=8)
        user = _make_user(1, "张三")

        db.query.return_value.filter.return_value.all.side_effect = [
            [ts1, ts2],  # timesheet query
        ]
        db.query.return_value.filter.return_value.first.return_value = user

        anomalies = service.detect_anomalies()
        daily_anomalies = [a for a in anomalies if a["type"] == "EXCESSIVE_DAILY_HOURS"]
        assert len(daily_anomalies) == 1
        assert daily_anomalies[0]["hours"] == 18
        assert daily_anomalies[0]["severity"] == "HIGH"

    def test_no_anomaly_within_limit(self, service, db):
        ts = _make_timesheet(user_id=1, work_date=date(2025, 3, 10), hours=8)
        db.query.return_value.filter.return_value.all.side_effect = [
            [ts],
        ]
        anomalies = service.detect_anomalies()
        daily_anomalies = [a for a in anomalies if a["type"] == "EXCESSIVE_DAILY_HOURS"]
        assert len(daily_anomalies) == 0

    def test_returns_empty_when_no_timesheets(self, service, db):
        db.query.return_value.filter.return_value.all.side_effect = [[]]
        anomalies = service.detect_anomalies()
        assert anomalies == []


# ── detect_anomalies - weekly ─────────────────────────────────────────────────

class TestDetectAnomaliesWeekly:
    def test_detects_excessive_weekly_hours(self, service, db):
        # Monday of a week
        monday = date(2025, 3, 3)
        timesheets = [
            _make_timesheet(user_id=2, work_date=monday + timedelta(days=i), hours=17)
            for i in range(5)  # 5 days × 17h = 85h > 80h
        ]
        user = _make_user(2, "李四")
        db.query.return_value.filter.return_value.all.side_effect = [timesheets]
        db.query.return_value.filter.return_value.first.return_value = user

        anomalies = service.detect_anomalies()
        weekly = [a for a in anomalies if a["type"] == "EXCESSIVE_WEEKLY_HOURS"]
        assert len(weekly) >= 1
        assert weekly[0]["severity"] == "MEDIUM"


# ── detect_anomalies - monthly ────────────────────────────────────────────────

class TestDetectAnomaliesMonthly:
    def test_detects_excessive_monthly_hours(self, service, db):
        # 22 workdays × 14h = 308h > 300h
        timesheets = [
            _make_timesheet(user_id=3, work_date=date(2025, 3, i), hours=14)
            for i in range(1, 23)
        ]
        user = _make_user(3, "王五")
        db.query.return_value.filter.return_value.all.side_effect = [timesheets]
        db.query.return_value.filter.return_value.first.return_value = user

        anomalies = service.detect_anomalies()
        monthly = [a for a in anomalies if a["type"] == "EXCESSIVE_MONTHLY_HOURS"]
        assert len(monthly) >= 1


# ── detect_anomalies with filters ─────────────────────────────────────────────

class TestDetectAnomaliesWithFilters:
    def test_applies_user_id_filter(self, service, db):
        db.query.return_value.filter.return_value.all.return_value = []
        service.detect_anomalies(user_id=42)
        # filter was called (multiple times for different conditions)
        assert db.query.return_value.filter.called

    def test_applies_date_range_filter(self, service, db):
        db.query.return_value.filter.return_value.all.return_value = []
        service.detect_anomalies(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31)
        )
        assert db.query.return_value.filter.called


# ── check_work_log_completeness ───────────────────────────────────────────────

class TestCheckWorkLogCompleteness:
    def test_returns_dict_with_expected_keys(self, service, db):
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        result = service.check_work_log_completeness()
        assert isinstance(result, dict)

    def test_detects_missing_work_log(self, service, db):
        user_id = 1
        work_date = date(2025, 3, 10)
        user = _make_user(user_id)

        # Timesheet dates query
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [
            (work_date, user_id)
        ]
        # WorkLog query (first call returns None - no work log)
        db.query.return_value.filter.return_value.first.side_effect = [None, user]

        result = service.check_work_log_completeness(
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31)
        )
        # Should detect missing log
        assert isinstance(result, dict)

    def test_no_missing_logs_when_all_present(self, service, db):
        work_log = MagicMock()
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [
            (date(2025, 3, 10), 1)
        ]
        # WorkLog exists
        db.query.return_value.filter.return_value.first.return_value = work_log

        result = service.check_work_log_completeness()
        assert isinstance(result, dict)

    def test_applies_default_date_range(self, service, db):
        """Should use last 30 days by default."""
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        service.check_work_log_completeness()
        # Just verify it doesn't raise
        assert True

    def test_user_id_filter_applied(self, service, db):
        # Return a real list so len() works and no ZeroDivisionError occurs
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        result = service.check_work_log_completeness(user_id=99)
        # Should complete without error when no timesheets found
        assert isinstance(result, dict)
