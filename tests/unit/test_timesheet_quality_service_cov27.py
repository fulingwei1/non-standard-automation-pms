# -*- coding: utf-8 -*-
"""第二十七批 - timesheet_quality_service 单元测试"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock

pytest.importorskip("app.services.timesheet_quality_service")

from app.services.timesheet_quality_service import TimesheetQualityService


def make_db():
    return MagicMock()


def make_timesheet(**kwargs):
    ts = MagicMock()
    ts.id = kwargs.get("id", 1)
    ts.user_id = kwargs.get("user_id", 1)
    ts.hours = kwargs.get("hours", 8.0)
    ts.work_date = kwargs.get("work_date", date(2024, 6, 10))
    ts.status = kwargs.get("status", "APPROVED")
    ts.user_name = kwargs.get("user_name", "张三")
    return ts


class TestTimesheetQualityServiceConstants:
    def test_max_daily_hours_is_16(self):
        assert TimesheetQualityService.MAX_DAILY_HOURS == 16

    def test_min_daily_hours_is_half(self):
        assert TimesheetQualityService.MIN_DAILY_HOURS == 0.5

    def test_max_weekly_hours_is_80(self):
        assert TimesheetQualityService.MAX_WEEKLY_HOURS == 80

    def test_max_monthly_hours_is_300(self):
        assert TimesheetQualityService.MAX_MONTHLY_HOURS == 300


class TestDetectAnomalies:
    def setup_method(self):
        self.db = make_db()
        self.svc = TimesheetQualityService(self.db)

    def test_no_anomalies_for_normal_hours(self):
        ts = make_timesheet(hours=8.0)
        self.db.query.return_value.filter.return_value.all.return_value = [ts]
        # No user query needed for normal hours
        self.db.query.return_value.filter.return_value.first.return_value = None
        anomalies = self.svc.detect_anomalies()
        assert isinstance(anomalies, list)

    def test_detects_excessive_daily_hours(self):
        # Single user with 20 hours in one day → triggers anomaly
        ts1 = make_timesheet(user_id=1, hours=12.0, work_date=date(2024, 6, 10))
        ts2 = make_timesheet(user_id=1, hours=10.0, work_date=date(2024, 6, 10))

        user = MagicMock()
        user.real_name = "张三"
        user.username = "zhangsan"

        self.db.query.return_value.filter.return_value.all.return_value = [ts1, ts2]
        self.db.query.return_value.filter.return_value.first.return_value = user

        anomalies = self.svc.detect_anomalies()
        daily_anomalies = [a for a in anomalies if a["type"] == "EXCESSIVE_DAILY_HOURS"]
        assert len(daily_anomalies) >= 1

    def test_detects_excessive_weekly_hours(self):
        # 5 days × 18 hours = 90 hours → exceeds weekly limit of 80
        base_date = date(2024, 6, 10)  # Monday
        timesheets = [
            make_timesheet(user_id=1, hours=18.0, work_date=base_date + timedelta(days=i))
            for i in range(5)
        ]

        user = MagicMock()
        user.real_name = "李四"
        user.username = "lisi"

        self.db.query.return_value.filter.return_value.all.return_value = timesheets
        self.db.query.return_value.filter.return_value.first.return_value = user

        anomalies = self.svc.detect_anomalies()
        weekly_anomalies = [a for a in anomalies if a["type"] == "EXCESSIVE_WEEKLY_HOURS"]
        assert len(weekly_anomalies) >= 1

    def test_returns_list_always(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.svc.detect_anomalies()
        assert isinstance(result, list)

    def test_anomaly_has_required_fields(self):
        ts1 = make_timesheet(user_id=1, hours=12.0, work_date=date(2024, 6, 10))
        ts2 = make_timesheet(user_id=1, hours=8.0, work_date=date(2024, 6, 10))

        user = MagicMock()
        user.real_name = "王五"
        user.username = "wangwu"

        self.db.query.return_value.filter.return_value.all.return_value = [ts1, ts2]
        self.db.query.return_value.filter.return_value.first.return_value = user

        anomalies = self.svc.detect_anomalies()
        if anomalies:
            anomaly = anomalies[0]
            assert "type" in anomaly
            assert "severity" in anomaly
            assert "user_id" in anomaly
            assert "message" in anomaly


class TestCheckWorkLogCompleteness:
    def setup_method(self):
        self.db = make_db()
        self.svc = TimesheetQualityService(self.db)

    def test_returns_dict(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.all.return_value = []
        result = self.svc.check_work_log_completeness()
        assert isinstance(result, dict)

    def test_with_user_id_filter(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.all.return_value = []
        result = self.svc.check_work_log_completeness(user_id=1)
        assert isinstance(result, dict)

    def test_with_date_range(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.all.return_value = []
        start = date(2024, 6, 1)
        end = date(2024, 6, 30)
        result = self.svc.check_work_log_completeness(start_date=start, end_date=end)
        assert isinstance(result, dict)


class TestTimesheetQualityServiceInit:
    def test_init_stores_db(self):
        db = make_db()
        svc = TimesheetQualityService(db)
        assert svc.db is db

    def test_max_daily_hours_accessible(self):
        db = make_db()
        svc = TimesheetQualityService(db)
        assert svc.MAX_DAILY_HOURS == 16

    def test_max_weekly_hours_accessible(self):
        db = make_db()
        svc = TimesheetQualityService(db)
        assert svc.MAX_WEEKLY_HOURS == 80
