# -*- coding: utf-8 -*-
"""Tests for alert trend service"""

from datetime import date, datetime


class MockAlertRecord:
    def __init__(self, alert_no, alert_level, alert_title, triggered_at, status, rule_type, rule=None):
        self.alert_no = alert_no
        self.alert_level = alert_level
        self.alert_title = alert_title
        self.triggered_at = triggered_at
        self.status = status
        self.rule_type = rule_type
        self.rule = rule


class MockAlertRule:
    def __init__(self, rule_type):
        self.rule_type = rule_type


class TestGetPeriodKey:
    def test_get_period_key_daily(self):
        from app.services.alert.alert_trend_service import get_period_key

        dt = datetime(2024, 2, 10, 15, 30, 0)
        assert get_period_key(dt, "DAILY") == "2024-02-10"

    def test_get_period_key_weekly(self):
        from app.services.alert.alert_trend_service import get_period_key

        dt = datetime(2024, 2, 10, 15, 30, 0)
        assert get_period_key(dt, "WEEKLY") == "2024-02-05"

    def test_get_period_key_monthly(self):
        from app.services.alert.alert_trend_service import get_period_key

        dt = datetime(2024, 2, 10, 15, 30, 0)
        assert get_period_key(dt, "MONTHLY") == "2024-02-01"

    def test_get_period_key_unknown_period(self):
        from app.services.alert.alert_trend_service import get_period_key

        dt = datetime(2024, 2, 10, 15, 30, 0)
        assert get_period_key(dt, "UNKNOWN") == "2024-02-10"


class TestGenerateDateRange:
    def test_generate_date_range_daily(self):
        from app.services.alert.alert_trend_service import generate_date_range

        assert generate_date_range(date(2024, 2, 1), date(2024, 2, 5), "DAILY") == [
            "2024-02-01",
            "2024-02-02",
            "2024-02-03",
            "2024-02-04",
            "2024-02-05",
        ]

    def test_generate_date_range_monthly(self):
        from app.services.alert.alert_trend_service import generate_date_range

        assert generate_date_range(date(2024, 1, 15), date(2024, 4, 10), "MONTHLY") == [
            "2024-01-01",
            "2024-02-01",
            "2024-03-01",
            "2024-04-01",
        ]

    def test_generate_date_range_single_day(self):
        from app.services.alert.alert_trend_service import generate_date_range

        assert generate_date_range(date(2024, 2, 1), date(2024, 2, 1), "DAILY") == ["2024-02-01"]


class TestBuildTrendStatistics:
    def test_build_trend_statistics_daily(self):
        from app.services.alert.alert_trend_service import build_trend_statistics

        alerts = [
            MockAlertRecord("ALT001", "WARNING", "进度延迟", datetime(2024, 2, 1, 10, 0), "RESOLVED", "PROGRESS", rule=MockAlertRule("PROGRESS")),
            MockAlertRecord("ALT002", "ERROR", "成本超支", datetime(2024, 2, 1, 14, 0), "OPEN", "COST", rule=MockAlertRule("COST")),
            MockAlertRecord("ALT003", "WARNING", "质量异常", datetime(2024, 2, 2, 9, 0), "RESOLVED", "QUALITY", rule=MockAlertRule("QUALITY")),
        ]
        stats = build_trend_statistics(alerts, "DAILY")
        assert stats["date_trends"]["2024-02-01"] == 2
        assert stats["date_trends"]["2024-02-02"] == 1
        assert stats["level_trends"]["2024-02-01"]["WARNING"] == 1
        assert stats["level_trends"]["2024-02-01"]["ERROR"] == 1

    def test_build_trend_statistics_with_null_triggered_at(self):
        from app.services.alert.alert_trend_service import build_trend_statistics

        alerts = [
            MockAlertRecord("ALT001", "WARNING", "进度延迟", None, "OPEN", "PROGRESS", rule=MockAlertRule("PROGRESS")),
            MockAlertRecord("ALT002", "ERROR", "成本超支", datetime(2024, 2, 1, 14, 0), "OPEN", "COST", rule=MockAlertRule("COST")),
        ]
        stats = build_trend_statistics(alerts, "DAILY")
        assert stats["date_trends"]["2024-02-01"] == 1


class TestBuildSummaryStatistics:
    def test_build_summary_statistics(self):
        from app.services.alert.alert_trend_service import build_summary_statistics

        alerts = [
            MockAlertRecord("ALT001", "WARNING", "进度延迟", datetime(2024, 2, 1, 10, 0), "RESOLVED", "PROGRESS", rule=MockAlertRule("PROGRESS")),
            MockAlertRecord("ALT002", "ERROR", "成本超支", datetime(2024, 2, 1, 14, 0), "OPEN", "COST", rule=MockAlertRule("COST")),
        ]
        stats = build_summary_statistics(alerts)
        assert stats["by_level"]["WARNING"] == 1
        assert stats["by_level"]["ERROR"] == 1
        assert stats["by_type"]["PROGRESS"] == 1
        assert stats["by_type"]["COST"] == 1
        assert stats["by_status"]["RESOLVED"] == 1
        assert stats["by_status"]["OPEN"] == 1

    def test_build_summary_statistics_with_nulls(self):
        from app.services.alert.alert_trend_service import build_summary_statistics

        alerts = [
            MockAlertRecord("ALT001", "WARNING", "进度延迟", datetime(2024, 2, 1, 10, 0), "OPEN", "PROGRESS", rule=MockAlertRule("PROGRESS")),
            MockAlertRecord("ALT002", None, "成本超支", datetime(2024, 2, 1, 14, 0), None, None, rule=None),
        ]
        stats = build_summary_statistics(alerts)
        assert stats["by_level"]["WARNING"] == 1
        assert stats["by_level"]["UNKNOWN"] == 1
        assert stats["by_type"]["PROGRESS"] == 1
        assert stats["by_type"]["UNKNOWN"] == 1
        assert stats["by_status"]["OPEN"] == 1
        assert stats["by_status"]["UNKNOWN"] == 1

    def test_build_summary_statistics_empty(self):
        from app.services.alert.alert_trend_service import build_summary_statistics

        assert build_summary_statistics([]) == {"by_level": {}, "by_type": {}, "by_status": {}}
