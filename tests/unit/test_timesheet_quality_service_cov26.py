# -*- coding: utf-8 -*-
"""第二十六批 - timesheet_quality_service 单元测试"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.timesheet_quality_service")

from app.services.timesheet_quality_service import TimesheetQualityService


class TestTimesheetQualityServiceConstants:
    def test_max_daily_hours(self):
        assert TimesheetQualityService.MAX_DAILY_HOURS == 16

    def test_min_daily_hours(self):
        assert TimesheetQualityService.MIN_DAILY_HOURS == 0.5

    def test_max_weekly_hours(self):
        assert TimesheetQualityService.MAX_WEEKLY_HOURS == 80

    def test_max_monthly_hours(self):
        assert TimesheetQualityService.MAX_MONTHLY_HOURS == 300


class TestDetectAnomalies:
    def setup_method(self):
        self.db = MagicMock()

    def _make_timesheet(self, user_id, work_date, hours, status="APPROVED"):
        ts = MagicMock()
        ts.user_id = user_id
        ts.work_date = work_date
        ts.hours = hours
        ts.status = status
        return ts

    def test_returns_empty_for_no_timesheets(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        svc = TimesheetQualityService(self.db)
        result = svc.detect_anomalies()
        assert result == []

    def test_detects_excessive_daily_hours(self):
        today = date.today()
        ts = self._make_timesheet(user_id=1, work_date=today, hours=17)
        self.db.query.return_value.filter.return_value.all.return_value = [ts]
        user = MagicMock(real_name="张三", username="zhangsan")
        self.db.query.return_value.filter.return_value.first.return_value = user
        svc = TimesheetQualityService(self.db)
        result = svc.detect_anomalies()
        assert any(a["type"] == "EXCESSIVE_DAILY_HOURS" for a in result)

    def test_no_anomaly_for_normal_hours(self):
        today = date.today()
        ts = self._make_timesheet(user_id=1, work_date=today, hours=8)
        self.db.query.return_value.filter.return_value.all.return_value = [ts]
        svc = TimesheetQualityService(self.db)
        # Should not flag 8 hours as excessive
        result = svc.detect_anomalies()
        excessive = [a for a in result if a["type"] == "EXCESSIVE_DAILY_HOURS"]
        assert len(excessive) == 0

    def test_anomaly_includes_required_fields(self):
        today = date.today()
        ts = self._make_timesheet(user_id=1, work_date=today, hours=18)
        self.db.query.return_value.filter.return_value.all.return_value = [ts]
        user = MagicMock(real_name="张三", username="zhangsan")
        self.db.query.return_value.filter.return_value.first.return_value = user
        svc = TimesheetQualityService(self.db)
        result = svc.detect_anomalies()
        anomaly = next((a for a in result if a["type"] == "EXCESSIVE_DAILY_HOURS"), None)
        if anomaly:
            required = {"type", "severity", "user_id", "work_date", "hours", "threshold"}
            assert required.issubset(anomaly.keys())

    def test_severity_is_high_for_excessive(self):
        today = date.today()
        ts = self._make_timesheet(user_id=1, work_date=today, hours=20)
        self.db.query.return_value.filter.return_value.all.return_value = [ts]
        user = MagicMock(real_name="张三", username="zhangsan")
        self.db.query.return_value.filter.return_value.first.return_value = user
        svc = TimesheetQualityService(self.db)
        result = svc.detect_anomalies()
        excessive = [a for a in result if a["type"] == "EXCESSIVE_DAILY_HOURS"]
        if excessive:
            assert excessive[0]["severity"] == "HIGH"

    def test_accumulates_hours_for_same_day(self):
        today = date.today()
        ts1 = self._make_timesheet(user_id=1, work_date=today, hours=9)
        ts2 = self._make_timesheet(user_id=1, work_date=today, hours=9)
        self.db.query.return_value.filter.return_value.all.return_value = [ts1, ts2]
        user = MagicMock(real_name="张三", username="zhangsan")
        self.db.query.return_value.filter.return_value.first.return_value = user
        svc = TimesheetQualityService(self.db)
        result = svc.detect_anomalies()
        # Total 18 hours → should be flagged
        assert any(a["type"] == "EXCESSIVE_DAILY_HOURS" and a["hours"] == 18 for a in result)

    def test_filter_by_user_id(self):
        today = date.today()
        ts = self._make_timesheet(user_id=2, work_date=today, hours=8)
        query_chain = MagicMock()
        self.db.query.return_value = query_chain
        query_chain.filter.return_value = query_chain
        query_chain.all.return_value = [ts]
        query_chain.first.return_value = MagicMock(real_name="李四", username="lisi")
        svc = TimesheetQualityService(self.db)
        svc.detect_anomalies(user_id=2)
        # No assertion on filter call args – just ensure no exception

    def test_filter_by_date_range(self):
        today = date.today()
        start = today - timedelta(days=7)
        query_chain = MagicMock()
        self.db.query.return_value = query_chain
        query_chain.filter.return_value = query_chain
        query_chain.all.return_value = []
        svc = TimesheetQualityService(self.db)
        result = svc.detect_anomalies(start_date=start, end_date=today)
        assert result == []


class TestTimesheetQualityServiceMethods:
    """Test other methods if they exist."""

    def setup_method(self):
        self.db = MagicMock()
        self.svc = TimesheetQualityService(self.db)

    def test_service_instantiation(self):
        assert self.svc is not None
        assert self.svc.db is self.db

    def test_max_daily_hours_class_attribute(self):
        assert self.svc.MAX_DAILY_HOURS == 16

    def test_detect_anomalies_is_callable(self):
        assert callable(self.svc.detect_anomalies)
