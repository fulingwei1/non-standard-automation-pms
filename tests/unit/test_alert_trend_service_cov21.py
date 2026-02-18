# -*- coding: utf-8 -*-
"""第二十一批：预警趋势分析服务单元测试"""

import pytest
from unittest.mock import MagicMock
from datetime import date, datetime, timedelta

pytest.importorskip("app.services.alert_trend_service")


def _make_alert(level="WARN", rule_type="SCHEDULE_DELAY", status="PENDING", days_ago=1):
    a = MagicMock()
    a.alert_level = level
    a.rule_type = rule_type
    a.status = status
    a.triggered_at = datetime.now() - timedelta(days=days_ago)
    return a


class TestGetPeriodKey:
    def test_daily_period(self):
        from app.services.alert_trend_service import get_period_key
        dt = datetime(2025, 6, 15, 10, 30)
        key = get_period_key(dt, "DAILY")
        assert key == "2025-06-15"

    def test_monthly_period(self):
        from app.services.alert_trend_service import get_period_key
        dt = datetime(2025, 6, 15, 10, 30)
        key = get_period_key(dt, "MONTHLY")
        assert key.startswith("2025-06")

    def test_weekly_period_returns_monday(self):
        from app.services.alert_trend_service import get_period_key
        # Wednesday 2025-06-11, Monday should be 2025-06-09
        dt = datetime(2025, 6, 11, 10, 0)
        key = get_period_key(dt, "WEEKLY")
        assert key == "2025-06-09"

    def test_unknown_period_defaults_to_daily(self):
        from app.services.alert_trend_service import get_period_key
        dt = datetime(2025, 6, 15)
        key = get_period_key(dt, "UNKNOWN")
        assert key == "2025-06-15"


class TestGenerateDateRange:
    def test_daily_range(self):
        from app.services.alert_trend_service import generate_date_range
        start = date(2025, 6, 1)
        end = date(2025, 6, 5)
        dates = generate_date_range(start, end, "DAILY")
        assert len(dates) == 5
        assert "2025-06-01" in dates
        assert "2025-06-05" in dates

    def test_monthly_range_single_month(self):
        from app.services.alert_trend_service import generate_date_range
        start = date(2025, 6, 1)
        end = date(2025, 6, 30)
        dates = generate_date_range(start, end, "MONTHLY")
        assert len(dates) >= 1
        assert "2025-06-01" in dates

    def test_weekly_range(self):
        from app.services.alert_trend_service import generate_date_range
        start = date(2025, 6, 2)  # Monday
        end = date(2025, 6, 15)
        dates = generate_date_range(start, end, "WEEKLY")
        assert len(dates) >= 2


class TestBuildTrendStatistics:
    def test_empty_alerts_returns_empty_dicts(self):
        from app.services.alert_trend_service import build_trend_statistics
        result = build_trend_statistics([], "DAILY")
        assert result["date_trends"] == {}
        assert result["level_trends"] == {}

    def test_counts_alerts_by_date(self):
        from app.services.alert_trend_service import build_trend_statistics
        alerts = [
            _make_alert(level="WARN", days_ago=0),
            _make_alert(level="HIGH", days_ago=0),
            _make_alert(level="WARN", days_ago=1),
        ]
        result = build_trend_statistics(alerts, "DAILY")
        today = date.today().isoformat()
        assert result["date_trends"].get(today, 0) == 2

    def test_skips_alerts_without_triggered_at(self):
        from app.services.alert_trend_service import build_trend_statistics
        a = MagicMock()
        a.triggered_at = None
        result = build_trend_statistics([a], "DAILY")
        assert result["date_trends"] == {}


class TestBuildSummaryStatistics:
    def test_empty_list_returns_empty_dicts(self):
        from app.services.alert_trend_service import build_summary_statistics
        result = build_summary_statistics([])
        assert result["by_level"] == {}
        assert result["by_type"] == {}
        assert result["by_status"] == {}

    def test_counts_by_level(self):
        from app.services.alert_trend_service import build_summary_statistics
        alerts = [
            _make_alert(level="WARN"),
            _make_alert(level="WARN"),
            _make_alert(level="HIGH"),
        ]
        result = build_summary_statistics(alerts)
        assert result["by_level"]["WARN"] == 2
        assert result["by_level"]["HIGH"] == 1

    def test_handles_none_fields(self):
        from app.services.alert_trend_service import build_summary_statistics
        a = MagicMock()
        a.alert_level = None
        a.rule_type = None
        a.status = None
        result = build_summary_statistics([a])
        assert result["by_level"].get("UNKNOWN", 0) == 1
