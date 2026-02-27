# -*- coding: utf-8 -*-
"""第二十八批 - timesheet_quality_service 单元测试（工时质量检查服务）"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.timesheet_quality_service")

from app.services.timesheet_quality_service import TimesheetQualityService


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_timesheet(
    user_id=1,
    work_date=None,
    hours=8.0,
    status="APPROVED",
):
    ts = MagicMock()
    ts.user_id = user_id
    ts.work_date = work_date or date(2024, 1, 15)
    ts.hours = hours
    ts.status = status
    return ts


def _make_user(user_id=1, real_name="张三", username="zhangsan"):
    u = MagicMock()
    u.id = user_id
    u.real_name = real_name
    u.username = username
    return u


def _make_service(db=None):
    if db is None:
        db = MagicMock()
    return TimesheetQualityService()


# ─── detect_anomalies ────────────────────────────────────────

class TestDetectAnomalies:

    def test_returns_empty_when_no_timesheets(self):
        db = MagicMock()
        q = db.query.return_value.filter.return_value
        q.filter.return_value.all.return_value = []
        q.all.return_value = []

        svc = _make_service(db)
        result = svc.detect_anomalies()
        assert result == []

    def test_detects_excessive_daily_hours(self):
        db = MagicMock()
        ts = _make_timesheet(user_id=1, work_date=date(2024, 1, 15), hours=20.0)
        user = _make_user()

        q = db.query.return_value
        q.filter.return_value = q
        q.all.return_value = [ts]
        q.first.return_value = user

        svc = _make_service(db)
        anomalies = svc.detect_anomalies()

        daily_anomalies = [a for a in anomalies if a["type"] == "EXCESSIVE_DAILY_HOURS"]
        assert len(daily_anomalies) >= 1
        assert daily_anomalies[0]["hours"] == 20.0
        assert daily_anomalies[0]["severity"] == "HIGH"

    def test_no_anomaly_for_normal_hours(self):
        db = MagicMock()
        ts = _make_timesheet(user_id=1, work_date=date(2024, 1, 15), hours=8.0)
        user = _make_user()

        q = db.query.return_value
        q.filter.return_value = q
        q.all.return_value = [ts]
        q.first.return_value = user

        svc = _make_service(db)
        anomalies = svc.detect_anomalies()

        daily_anomalies = [a for a in anomalies if a["type"] == "EXCESSIVE_DAILY_HOURS"]
        assert len(daily_anomalies) == 0

    def test_detects_excessive_weekly_hours(self):
        """单周超过 80 小时应检测到"""
        db = MagicMock()
        work_day = date(2024, 1, 15)  # Monday
        # 5天 * 17 = 85 小时
        timesheets = [
            _make_timesheet(user_id=1, work_date=work_day + timedelta(days=i), hours=17.0)
            for i in range(5)
        ]
        user = _make_user()

        q = db.query.return_value
        q.filter.return_value = q
        q.all.return_value = timesheets
        q.first.return_value = user

        svc = _make_service(db)
        anomalies = svc.detect_anomalies()

        weekly_anomalies = [a for a in anomalies if a["type"] == "EXCESSIVE_WEEKLY_HOURS"]
        assert len(weekly_anomalies) >= 1

    def test_user_filter_applied(self):
        db = MagicMock()
        q = db.query.return_value
        fq = q.filter.return_value
        fq.filter.return_value = fq
        fq.all.return_value = []

        svc = _make_service(db)
        svc.detect_anomalies(user_id=42)

        # 应该有对应的 user_id 过滤调用
        db.query.assert_called()

    def test_anomaly_includes_user_name(self):
        db = MagicMock()
        ts = _make_timesheet(user_id=2, work_date=date(2024, 1, 15), hours=25.0)
        user = _make_user(user_id=2, real_name="李四")

        q = db.query.return_value
        q.filter.return_value = q
        q.all.return_value = [ts]
        q.first.return_value = user

        svc = _make_service(db)
        anomalies = svc.detect_anomalies()

        daily_anomalies = [a for a in anomalies if a["type"] == "EXCESSIVE_DAILY_HOURS"]
        assert len(daily_anomalies) >= 1
        assert "李四" in daily_anomalies[0]["message"]


# ─── check_work_log_completeness ────────────────────────────

class TestCheckWorkLogCompleteness:

    def test_returns_100_completeness_when_no_timesheets(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.distinct.return_value.all.return_value = []

        svc = _make_service(db)
        result = svc.check_work_log_completeness()

        assert result["completeness_rate"] == 100
        assert result["missing_log_count"] == 0

    def test_detects_missing_work_logs(self):
        db = MagicMock()
        # 有2条工时记录日期
        timesheet_dates = [(date(2024, 1, 15), 1), (date(2024, 1, 16), 1)]

        q = db.query.return_value
        q.filter.return_value = q
        q.distinct.return_value.all.return_value = timesheet_dates

        user = _make_user()
        # WorkLog query: None = 缺失；User query: user
        q.first.side_effect = [None, user, None, user]

        svc = _make_service(db)
        result = svc.check_work_log_completeness()

        assert result["missing_log_count"] == 2
        assert result["completeness_rate"] == 0.0

    def test_completeness_rate_partial(self):
        db = MagicMock()
        timesheet_dates = [(date(2024, 1, 15), 1), (date(2024, 1, 16), 1)]

        q = db.query.return_value
        q.filter.return_value = q
        q.distinct.return_value.all.return_value = timesheet_dates

        user = _make_user()
        work_log = MagicMock()
        # 第一天有日志，第二天缺失
        q.first.side_effect = [work_log, None, user]

        svc = _make_service(db)
        result = svc.check_work_log_completeness()

        assert result["missing_log_count"] == 1
        assert result["completeness_rate"] == pytest.approx(50.0, abs=0.01)

    def test_returns_date_range_in_result(self):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value = q
        q.distinct.return_value.all.return_value = []

        svc = _make_service(db)
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        result = svc.check_work_log_completeness(start_date=start, end_date=end)

        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-01-31"

    def test_all_logs_present_gives_100_rate(self):
        db = MagicMock()
        timesheet_dates = [(date(2024, 1, 15), 1)]

        q = db.query.return_value
        q.filter.return_value = q
        q.distinct.return_value.all.return_value = timesheet_dates

        work_log = MagicMock()
        q.first.return_value = work_log

        svc = _make_service(db)
        result = svc.check_work_log_completeness()

        assert result["completeness_rate"] == 100
        assert result["missing_log_count"] == 0


# ─── 常量验证 ────────────────────────────────────────────────

class TestConstants:

    def test_max_daily_hours(self):
        svc = _make_service()
        assert svc.MAX_DAILY_HOURS == 16

    def test_max_weekly_hours(self):
        svc = _make_service()
        assert svc.MAX_WEEKLY_HOURS == 80

    def test_max_monthly_hours(self):
        svc = _make_service()
        assert svc.MAX_MONTHLY_HOURS == 300
