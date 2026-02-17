# -*- coding: utf-8 -*-
"""
工时异常检测服务单元测试 (I3组)
测试 TimesheetAnomalyDetector 各方法
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

import pytest

from app.services.timesheet_reminder.anomaly_detector import TimesheetAnomalyDetector


def _make_detector():
    db = MagicMock()
    with patch("app.services.timesheet_reminder.anomaly_detector.TimesheetReminderManager") as mock_rm:
        mock_rm.return_value = MagicMock()
        detector = TimesheetAnomalyDetector(db)
        detector.db = db
    return detector


def _setup_query_returning(detector, items):
    """让 detector.db.query() chain 返回 items"""
    q = MagicMock()
    q.filter.return_value = q
    q.group_by.return_value = q
    q.having.return_value = q
    q.distinct.return_value = q
    q.order_by.return_value = q
    q.all.return_value = items
    q.first.return_value = None
    detector.db.query.return_value = q
    return q


# ─────────────────────────────────────────────────────────────────────────────
# detect_daily_over_12
# ─────────────────────────────────────────────────────────────────────────────
class TestDetectDailyOver12:
    def test_no_results_returns_empty(self):
        detector = _make_detector()
        _setup_query_returning(detector, [])
        result = detector.detect_daily_over_12(date(2024, 1, 1), date(2024, 1, 7))
        assert result == []

    def test_existing_anomaly_skipped(self):
        detector = _make_detector()
        r = MagicMock()
        r.user_id = 1; r.user_name = "Tom"; r.work_date = date(2024, 1, 1)
        r.total_hours = Decimal("13"); r.timesheet_ids = "5,6"

        q = MagicMock()
        q.filter.return_value = q
        q.group_by.return_value = q
        q.having.return_value = q
        q.all.return_value = [r]
        q.first.return_value = MagicMock()  # existing record found
        detector.db.query.return_value = q

        result = detector.detect_daily_over_12(date(2024, 1, 1), date(2024, 1, 7))
        assert result == []

    def test_creates_anomaly_record(self):
        detector = _make_detector()
        r = MagicMock()
        r.user_id = 1; r.user_name = "Tom"; r.work_date = date(2024, 1, 1)
        r.total_hours = Decimal("14"); r.timesheet_ids = "5,6"

        q_having = MagicMock()
        q_having.all.return_value = [r]

        q_existing = MagicMock()
        q_existing.filter.return_value = q_existing
        q_existing.first.return_value = None  # no existing

        q = MagicMock()
        q.filter.return_value = q
        q.group_by.return_value = q
        q.having.return_value = q_having

        # Second query (for existing check) returns q_existing
        detector.db.query.side_effect = [q, q_existing]

        anomaly = MagicMock()
        detector.reminder_manager.create_anomaly_record.return_value = anomaly

        result = detector.detect_daily_over_12(date(2024, 1, 1), date(2024, 1, 7))
        assert len(result) == 1
        detector.reminder_manager.create_anomaly_record.assert_called_once()

    def test_with_user_id_filter(self):
        detector = _make_detector()
        _setup_query_returning(detector, [])
        result = detector.detect_daily_over_12(date(2024, 1, 1), date(2024, 1, 7), user_id=5)
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# detect_daily_invalid
# ─────────────────────────────────────────────────────────────────────────────
class TestDetectDailyInvalid:
    def test_no_results_returns_empty(self):
        detector = _make_detector()
        _setup_query_returning(detector, [])
        result = detector.detect_daily_invalid(date(2024, 1, 1), date(2024, 1, 7))
        assert result == []

    def test_creates_anomaly_for_invalid_hours(self):
        detector = _make_detector()
        r = MagicMock()
        r.user_id = 2; r.user_name = "Jane"; r.work_date = date(2024, 1, 2)
        r.total_hours = Decimal("25"); r.timesheet_ids = "10"

        q_having = MagicMock(); q_having.all.return_value = [r]
        q_existing = MagicMock(); q_existing.filter.return_value = q_existing; q_existing.first.return_value = None

        q = MagicMock()
        q.filter.return_value = q
        q.group_by.return_value = q
        q.having.return_value = q_having

        detector.db.query.side_effect = [q, q_existing]
        anomaly = MagicMock()
        detector.reminder_manager.create_anomaly_record.return_value = anomaly

        result = detector.detect_daily_invalid(date(2024, 1, 1), date(2024, 1, 7))
        assert len(result) == 1


# ─────────────────────────────────────────────────────────────────────────────
# detect_weekly_over_60
# ─────────────────────────────────────────────────────────────────────────────
class TestDetectWeeklyOver60:
    def test_no_results_returns_empty(self):
        detector = _make_detector()
        _setup_query_returning(detector, [])
        result = detector.detect_weekly_over_60(date(2024, 1, 1), date(2024, 1, 7))
        assert result == []

    def test_creates_anomaly_for_weekly_over_60(self):
        detector = _make_detector()
        r = MagicMock()
        r.user_id = 1; r.user_name = "Bob"; r.weekly_hours = Decimal("65")
        r.timesheet_ids = "1,2,3"

        q_having = MagicMock(); q_having.all.return_value = [r]
        q_existing = MagicMock(); q_existing.filter.return_value = q_existing; q_existing.first.return_value = None

        q = MagicMock()
        q.filter.return_value = q
        q.group_by.return_value = q
        q.having.return_value = q_having

        detector.db.query.side_effect = [q, q_existing]
        anomaly = MagicMock()
        detector.reminder_manager.create_anomaly_record.return_value = anomaly

        result = detector.detect_weekly_over_60(date(2024, 1, 1), date(2024, 1, 7))
        assert len(result) == 1

    def test_spans_multiple_weeks(self):
        detector = _make_detector()
        _setup_query_returning(detector, [])
        # 14-day range covers 2 weeks
        result = detector.detect_weekly_over_60(date(2024, 1, 1), date(2024, 1, 14))
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# detect_no_rest_7days
# ─────────────────────────────────────────────────────────────────────────────
class TestDetectNoRest7Days:
    def test_no_users_returns_empty(self):
        detector = _make_detector()
        _setup_query_returning(detector, [])
        result = detector.detect_no_rest_7days(date(2024, 1, 1), date(2024, 1, 14))
        assert result == []

    def test_user_with_less_than_7_days_no_anomaly(self):
        detector = _make_detector()
        user = MagicMock(); user.user_id = 1; user.user_name = "Alice"

        # Work dates - only 5 days
        work_dates = [MagicMock(work_date=date(2024, 1, i)) for i in range(1, 6)]

        q_users = MagicMock(); q_users.filter.return_value = q_users; q_users.distinct.return_value = q_users
        q_users.all.return_value = [user]

        q_dates = MagicMock(); q_dates.filter.return_value = q_dates; q_dates.distinct.return_value = q_dates
        q_dates.order_by.return_value = q_dates; q_dates.all.return_value = work_dates

        detector.db.query.side_effect = [q_users, q_dates]
        result = detector.detect_no_rest_7days(date(2024, 1, 1), date(2024, 1, 14))
        assert result == []

    def test_detects_7_consecutive_days(self):
        detector = _make_detector()
        user = MagicMock(); user.user_id = 1; user.user_name = "Alice"

        # 7 consecutive work days
        work_dates_obj = [MagicMock(work_date=date(2024, 1, i)) for i in range(1, 8)]

        q_users = MagicMock()
        q_users.filter.return_value = q_users; q_users.distinct.return_value = q_users
        q_users.all.return_value = [user]

        q_dates = MagicMock()
        q_dates.filter.return_value = q_dates; q_dates.distinct.return_value = q_dates
        q_dates.order_by.return_value = q_dates
        q_dates.all.return_value = work_dates_obj

        q_existing = MagicMock()
        q_existing.filter.return_value = q_existing; q_existing.first.return_value = None

        q_ids = MagicMock()
        q_ids.filter.return_value = q_ids
        q_ids.all.return_value = [MagicMock(id=i) for i in range(1, 8)]

        detector.db.query.side_effect = [q_users, q_dates, q_existing, q_ids]
        anomaly = MagicMock()
        detector.reminder_manager.create_anomaly_record.return_value = anomaly

        result = detector.detect_no_rest_7days(date(2024, 1, 1), date(2024, 1, 14))
        assert len(result) == 1


# ─────────────────────────────────────────────────────────────────────────────
# detect_progress_mismatch
# ─────────────────────────────────────────────────────────────────────────────
class TestDetectProgressMismatch:
    def test_no_timesheets_returns_empty(self):
        detector = _make_detector()
        _setup_query_returning(detector, [])
        result = detector.detect_progress_mismatch(date(2024, 1, 1), date(2024, 1, 7))
        assert result == []

    def test_hours_less_than_4_not_anomaly(self):
        detector = _make_detector()
        ts = MagicMock()
        ts.id = 1; ts.user_id = 1; ts.user_name = "Tom"; ts.task_id = 5
        ts.work_date = date(2024, 1, 1); ts.hours = Decimal("3")
        ts.progress_before = 20; ts.progress_after = 20  # no change

        _setup_query_returning(detector, [ts])
        result = detector.detect_progress_mismatch(date(2024, 1, 1), date(2024, 1, 7))
        assert result == []

    def test_4_hours_no_progress_creates_anomaly(self):
        detector = _make_detector()
        ts = MagicMock()
        ts.id = 1; ts.user_id = 1; ts.user_name = "Tom"; ts.task_id = 5
        ts.work_date = date(2024, 1, 1); ts.hours = Decimal("4")
        ts.progress_before = 20; ts.progress_after = 20  # 0 change

        q_ts = MagicMock(); q_ts.filter.return_value = q_ts; q_ts.all.return_value = [ts]
        q_existing = MagicMock(); q_existing.filter.return_value = q_existing; q_existing.first.return_value = None
        detector.db.query.side_effect = [q_ts, q_existing]

        anomaly = MagicMock()
        detector.reminder_manager.create_anomaly_record.return_value = anomaly
        result = detector.detect_progress_mismatch(date(2024, 1, 1), date(2024, 1, 7))
        assert len(result) == 1

    def test_8_hours_small_progress_creates_anomaly(self):
        detector = _make_detector()
        ts = MagicMock()
        ts.id = 2; ts.user_id = 2; ts.user_name = "Jane"; ts.task_id = 6
        ts.work_date = date(2024, 1, 2); ts.hours = Decimal("8")
        ts.progress_before = 50; ts.progress_after = 55  # only 5% change

        q_ts = MagicMock(); q_ts.filter.return_value = q_ts; q_ts.all.return_value = [ts]
        q_existing = MagicMock(); q_existing.filter.return_value = q_existing; q_existing.first.return_value = None
        detector.db.query.side_effect = [q_ts, q_existing]

        anomaly = MagicMock()
        detector.reminder_manager.create_anomaly_record.return_value = anomaly
        result = detector.detect_progress_mismatch(date(2024, 1, 1), date(2024, 1, 7))
        assert len(result) == 1

    def test_existing_anomaly_skipped(self):
        detector = _make_detector()
        ts = MagicMock()
        ts.id = 3; ts.user_id = 3; ts.user_name = "Bob"; ts.task_id = 7
        ts.work_date = date(2024, 1, 3); ts.hours = Decimal("5")
        ts.progress_before = 10; ts.progress_after = 10

        q_ts = MagicMock(); q_ts.filter.return_value = q_ts; q_ts.all.return_value = [ts]
        q_existing = MagicMock(); q_existing.filter.return_value = q_existing
        q_existing.first.return_value = MagicMock()  # existing anomaly
        detector.db.query.side_effect = [q_ts, q_existing]

        result = detector.detect_progress_mismatch(date(2024, 1, 1), date(2024, 1, 7))
        assert result == []

    def test_no_progress_fields_skipped(self):
        detector = _make_detector()
        ts = MagicMock()
        ts.id = 4; ts.task_id = 8
        ts.hours = Decimal("8")
        ts.progress_before = None; ts.progress_after = None

        _setup_query_returning(detector, [ts])
        result = detector.detect_progress_mismatch(date(2024, 1, 1), date(2024, 1, 7))
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# detect_all_anomalies
# ─────────────────────────────────────────────────────────────────────────────
class TestDetectAllAnomalies:
    def test_calls_all_detect_methods(self):
        detector = _make_detector()
        with patch.object(detector, "detect_daily_over_12", return_value=[]) as m1, \
             patch.object(detector, "detect_daily_invalid", return_value=[]) as m2, \
             patch.object(detector, "detect_weekly_over_60", return_value=[]) as m3, \
             patch.object(detector, "detect_no_rest_7days", return_value=[]) as m4, \
             patch.object(detector, "detect_progress_mismatch", return_value=[]) as m5:
            result = detector.detect_all_anomalies()
        assert result == []
        m1.assert_called_once(); m2.assert_called_once(); m3.assert_called_once()
        m4.assert_called_once(); m5.assert_called_once()

    def test_uses_default_dates_when_none(self):
        detector = _make_detector()
        with patch.object(detector, "detect_daily_over_12", return_value=[]) as m1, \
             patch.object(detector, "detect_daily_invalid", return_value=[]) as m2, \
             patch.object(detector, "detect_weekly_over_60", return_value=[]) as m3, \
             patch.object(detector, "detect_no_rest_7days", return_value=[]) as m4, \
             patch.object(detector, "detect_progress_mismatch", return_value=[]) as m5:
            result = detector.detect_all_anomalies()
        # Verify dates were provided
        args1 = m1.call_args[0]
        assert args1[0] is not None  # start_date
        assert args1[1] is not None  # end_date

    def test_combines_results_from_all_methods(self):
        detector = _make_detector()
        a1 = MagicMock(); a2 = MagicMock(); a3 = MagicMock()
        with patch.object(detector, "detect_daily_over_12", return_value=[a1]), \
             patch.object(detector, "detect_daily_invalid", return_value=[a2]), \
             patch.object(detector, "detect_weekly_over_60", return_value=[a3]), \
             patch.object(detector, "detect_no_rest_7days", return_value=[]), \
             patch.object(detector, "detect_progress_mismatch", return_value=[]):
            result = detector.detect_all_anomalies()
        assert len(result) == 3
        assert a1 in result and a2 in result and a3 in result

    def test_with_explicit_dates_and_user_id(self):
        detector = _make_detector()
        with patch.object(detector, "detect_daily_over_12", return_value=[]) as m1, \
             patch.object(detector, "detect_daily_invalid", return_value=[]) as m2, \
             patch.object(detector, "detect_weekly_over_60", return_value=[]) as m3, \
             patch.object(detector, "detect_no_rest_7days", return_value=[]) as m4, \
             patch.object(detector, "detect_progress_mismatch", return_value=[]) as m5:
            result = detector.detect_all_anomalies(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                user_id=42
            )
        # All methods should receive the same args
        m1.assert_called_once_with(date(2024, 1, 1), date(2024, 1, 31), 42)
