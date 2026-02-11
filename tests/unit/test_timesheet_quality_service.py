# -*- coding: utf-8 -*-
"""Tests for timesheet_quality_service.py"""
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

from app.services.timesheet_quality_service import TimesheetQualityService


class TestDetectAnomalies:
    def setup_method(self):
        self.db = MagicMock()
        self.service = TimesheetQualityService(self.db)

    def test_no_anomalies(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.service.detect_anomalies()
        assert result == []

    def test_excessive_daily_hours(self):
        ts = MagicMock(user_id=1, work_date=date(2025, 1, 6), hours=20, status="APPROVED")
        self.db.query.return_value.filter.return_value.all.return_value = [ts]
        user = MagicMock(real_name="张三", username="zhangsan")
        self.db.query.return_value.filter.return_value.first.return_value = user
        result = self.service.detect_anomalies()
        assert any(a['type'] == 'EXCESSIVE_DAILY_HOURS' for a in result)

    def test_excessive_weekly_hours(self):
        # 5 days × 17h = 85h > 80h weekly limit
        timesheets = []
        for i in range(5):
            ts = MagicMock(user_id=1, work_date=date(2025, 1, 6) + timedelta(days=i), hours=17)
            timesheets.append(ts)
        self.db.query.return_value.filter.return_value.all.return_value = timesheets
        user = MagicMock(real_name="张三", username="zhangsan")
        self.db.query.return_value.filter.return_value.first.return_value = user
        result = self.service.detect_anomalies()
        assert any(a['type'] == 'EXCESSIVE_WEEKLY_HOURS' for a in result)


class TestCheckWorkLogCompleteness:
    def setup_method(self):
        self.db = MagicMock()
        self.service = TimesheetQualityService(self.db)

    def test_no_timesheets(self):
        self.db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        result = self.service.check_work_log_completeness()
        assert result['missing_log_count'] == 0
        assert result['completeness_rate'] == 100

    def test_missing_logs(self):
        self.db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [
            (date(2025, 1, 6), 1),
        ]
        # WorkLog query returns None (missing)
        user = MagicMock(real_name="张三", username="zhangsan")
        self.db.query.return_value.filter.return_value.first.side_effect = [None, user]
        result = self.service.check_work_log_completeness()
        assert result['missing_log_count'] == 1


class TestCheckLaborLawCompliance:
    def setup_method(self):
        self.db = MagicMock()
        self.service = TimesheetQualityService(self.db)

    @patch("app.services.timesheet_quality_service.get_month_range_by_ym", return_value=(date(2025, 1, 1), date(2025, 1, 31)))
    def test_compliant(self, mock_range):
        ts = MagicMock(hours=10, overtime_type="OVERTIME")
        self.db.query.return_value.filter.return_value.all.return_value = [ts]
        result = self.service.check_labor_law_compliance(1, 2025, 1)
        assert result['is_compliant'] is True

    @patch("app.services.timesheet_quality_service.get_month_range_by_ym", return_value=(date(2025, 1, 1), date(2025, 1, 31)))
    def test_non_compliant(self, mock_range):
        ts = MagicMock(hours=40, overtime_type="OVERTIME")
        self.db.query.return_value.filter.return_value.all.return_value = [ts]
        result = self.service.check_labor_law_compliance(1, 2025, 1)
        assert result['is_compliant'] is False
        assert result['violation_hours'] == 4
