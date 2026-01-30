# -*- coding: utf-8 -*-
"""
AlertTrendService 综合单元测试

测试覆盖:
- get_period_key: 根据周期生成分组键
- generate_date_range: 生成日期范围
- build_trend_statistics: 构建趋势统计数据
- build_summary_statistics: 构建汇总统计
"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

import pytest


class TestGetPeriodKey:
    """测试 get_period_key 函数"""

    def test_returns_date_for_daily_period(self):
        """测试日周期返回日期"""
        from app.services.alert_trend_service import get_period_key

        dt = datetime(2026, 1, 15, 10, 30, 0)

        result = get_period_key(dt, "DAILY")

        assert result == "2026-01-15"

    def test_returns_monday_for_weekly_period(self):
        """测试周周期返回周一"""
        from app.services.alert_trend_service import get_period_key

        # 2026-01-15 is a Thursday
        dt = datetime(2026, 1, 15, 10, 30, 0)

        result = get_period_key(dt, "WEEKLY")

        assert result == "2026-01-12"  # Monday of that week

    def test_returns_first_day_for_monthly_period(self):
        """测试月周期返回月初"""
        from app.services.alert_trend_service import get_period_key

        dt = datetime(2026, 1, 15, 10, 30, 0)

        result = get_period_key(dt, "MONTHLY")

        assert result == "2026-01-01"

    def test_returns_date_for_unknown_period(self):
        """测试未知周期返回日期"""
        from app.services.alert_trend_service import get_period_key

        dt = datetime(2026, 1, 15, 10, 30, 0)

        result = get_period_key(dt, "UNKNOWN")

        assert result == "2026-01-15"

    def test_handles_monday_correctly(self):
        """测试正确处理周一"""
        from app.services.alert_trend_service import get_period_key

        # 2026-01-12 is a Monday
        dt = datetime(2026, 1, 12, 10, 30, 0)

        result = get_period_key(dt, "WEEKLY")

        assert result == "2026-01-12"

    def test_handles_sunday_correctly(self):
        """测试正确处理周日"""
        from app.services.alert_trend_service import get_period_key

        # 2026-01-18 is a Sunday
        dt = datetime(2026, 1, 18, 10, 30, 0)

        result = get_period_key(dt, "WEEKLY")

        assert result == "2026-01-12"  # Monday of that week


class TestGenerateDateRange:
    """测试 generate_date_range 函数"""

    def test_generates_daily_range(self):
        """测试生成日范围"""
        from app.services.alert_trend_service import generate_date_range

        start = date(2026, 1, 1)
        end = date(2026, 1, 5)

        result = generate_date_range(start, end, "DAILY")

        assert len(result) == 5
        assert result[0] == "2026-01-01"
        assert result[-1] == "2026-01-05"

    def test_generates_weekly_range(self):
        """测试生成周范围"""
        from app.services.alert_trend_service import generate_date_range

        start = date(2026, 1, 1)
        end = date(2026, 1, 31)

        result = generate_date_range(start, end, "WEEKLY")

        # Should have around 5 weeks
        assert len(result) >= 4
        # All should be Mondays
        for d in result:
            dt = date.fromisoformat(d)
            assert dt.weekday() == 0 or dt == start.replace(day=1) - timedelta(days=start.weekday())

    def test_generates_monthly_range(self):
        """测试生成月范围"""
        from app.services.alert_trend_service import generate_date_range

        start = date(2026, 1, 15)
        end = date(2026, 4, 15)

        result = generate_date_range(start, end, "MONTHLY")

        assert len(result) == 4
        assert result[0] == "2026-01-01"
        assert result[-1] == "2026-04-01"

    def test_handles_single_day(self):
        """测试处理单天"""
        from app.services.alert_trend_service import generate_date_range

        start = date(2026, 1, 15)
        end = date(2026, 1, 15)

        result = generate_date_range(start, end, "DAILY")

        assert result == ["2026-01-15"]

    def test_handles_year_boundary(self):
        """测试处理年边界"""
        from app.services.alert_trend_service import generate_date_range

        start = date(2025, 12, 1)
        end = date(2026, 2, 1)

        result = generate_date_range(start, end, "MONTHLY")

        assert "2025-12-01" in result
        assert "2026-01-01" in result
        assert "2026-02-01" in result

    def test_returns_sorted_dates(self):
        """测试返回排序的日期"""
        from app.services.alert_trend_service import generate_date_range

        start = date(2026, 1, 1)
        end = date(2026, 1, 10)

        result = generate_date_range(start, end, "DAILY")

        assert result == sorted(result)


class TestBuildTrendStatistics:
    """测试 build_trend_statistics 函数"""

    def test_returns_empty_when_no_alerts(self):
        """测试无预警时返回空"""
        from app.services.alert_trend_service import build_trend_statistics

        result = build_trend_statistics([], "DAILY")

        assert result["date_trends"] == {}
        assert result["level_trends"] == {}
        assert result["type_trends"] == {}
        assert result["status_trends"] == {}

    def test_counts_by_date(self):
        """测试按日期计数"""
        from app.services.alert_trend_service import build_trend_statistics

        mock_alert1 = MagicMock()
        mock_alert1.triggered_at = datetime(2026, 1, 15, 10, 0, 0)
        mock_alert1.alert_level = "WARNING"
        mock_alert1.rule_type = "PROGRESS"
        mock_alert1.status = "PENDING"

        mock_alert2 = MagicMock()
        mock_alert2.triggered_at = datetime(2026, 1, 15, 14, 0, 0)
        mock_alert2.alert_level = "CRITICAL"
        mock_alert2.rule_type = "COST"
        mock_alert2.status = "RESOLVED"

        result = build_trend_statistics([mock_alert1, mock_alert2], "DAILY")

        assert result["date_trends"]["2026-01-15"] == 2

    def test_groups_by_level(self):
        """测试按级别分组"""
        from app.services.alert_trend_service import build_trend_statistics

        mock_alert1 = MagicMock()
        mock_alert1.triggered_at = datetime(2026, 1, 15, 10, 0, 0)
        mock_alert1.alert_level = "WARNING"
        mock_alert1.rule_type = "PROGRESS"
        mock_alert1.status = "PENDING"

        mock_alert2 = MagicMock()
        mock_alert2.triggered_at = datetime(2026, 1, 15, 14, 0, 0)
        mock_alert2.alert_level = "WARNING"
        mock_alert2.rule_type = "COST"
        mock_alert2.status = "RESOLVED"

        result = build_trend_statistics([mock_alert1, mock_alert2], "DAILY")

        assert result["level_trends"]["2026-01-15"]["WARNING"] == 2

    def test_groups_by_type(self):
        """测试按类型分组"""
        from app.services.alert_trend_service import build_trend_statistics

        mock_alert = MagicMock()
        mock_alert.triggered_at = datetime(2026, 1, 15, 10, 0, 0)
        mock_alert.alert_level = "WARNING"
        mock_alert.rule_type = "PROGRESS_DELAY"
        mock_alert.status = "PENDING"

        result = build_trend_statistics([mock_alert], "DAILY")

        assert result["type_trends"]["2026-01-15"]["PROGRESS_DELAY"] == 1

    def test_groups_by_status(self):
        """测试按状态分组"""
        from app.services.alert_trend_service import build_trend_statistics

        mock_alert = MagicMock()
        mock_alert.triggered_at = datetime(2026, 1, 15, 10, 0, 0)
        mock_alert.alert_level = "WARNING"
        mock_alert.rule_type = "PROGRESS"
        mock_alert.status = "RESOLVED"

        result = build_trend_statistics([mock_alert], "DAILY")

        assert result["status_trends"]["2026-01-15"]["RESOLVED"] == 1

    def test_handles_missing_triggered_at(self):
        """测试处理缺失触发时间"""
        from app.services.alert_trend_service import build_trend_statistics

        mock_alert = MagicMock()
        mock_alert.triggered_at = None

        result = build_trend_statistics([mock_alert], "DAILY")

        assert result["date_trends"] == {}

    def test_handles_unknown_values(self):
        """测试处理未知值"""
        from app.services.alert_trend_service import build_trend_statistics

        mock_alert = MagicMock()
        mock_alert.triggered_at = datetime(2026, 1, 15, 10, 0, 0)
        mock_alert.alert_level = None
        mock_alert.rule_type = None
        mock_alert.status = None

        result = build_trend_statistics([mock_alert], "DAILY")

        assert result["level_trends"]["2026-01-15"]["UNKNOWN"] == 1
        assert result["type_trends"]["2026-01-15"]["UNKNOWN"] == 1
        assert result["status_trends"]["2026-01-15"]["UNKNOWN"] == 1

    def test_weekly_period_grouping(self):
        """测试周周期分组"""
        from app.services.alert_trend_service import build_trend_statistics

        # 2026-01-15 (Thursday) and 2026-01-16 (Friday) should be in same week
        mock_alert1 = MagicMock()
        mock_alert1.triggered_at = datetime(2026, 1, 15, 10, 0, 0)
        mock_alert1.alert_level = "WARNING"
        mock_alert1.rule_type = "PROGRESS"
        mock_alert1.status = "PENDING"

        mock_alert2 = MagicMock()
        mock_alert2.triggered_at = datetime(2026, 1, 16, 14, 0, 0)
        mock_alert2.alert_level = "WARNING"
        mock_alert2.rule_type = "PROGRESS"
        mock_alert2.status = "PENDING"

        result = build_trend_statistics([mock_alert1, mock_alert2], "WEEKLY")

        # Both should be grouped under the Monday of that week
        assert result["date_trends"]["2026-01-12"] == 2


class TestBuildSummaryStatistics:
    """测试 build_summary_statistics 函数"""

    def test_returns_empty_when_no_alerts(self):
        """测试无预警时返回空"""
        from app.services.alert_trend_service import build_summary_statistics

        result = build_summary_statistics([])

        assert result["by_level"] == {}
        assert result["by_type"] == {}
        assert result["by_status"] == {}

    def test_counts_by_level(self):
        """测试按级别计数"""
        from app.services.alert_trend_service import build_summary_statistics

        mock_alert1 = MagicMock()
        mock_alert1.alert_level = "WARNING"
        mock_alert1.rule_type = "PROGRESS"
        mock_alert1.status = "PENDING"

        mock_alert2 = MagicMock()
        mock_alert2.alert_level = "CRITICAL"
        mock_alert2.rule_type = "COST"
        mock_alert2.status = "RESOLVED"

        mock_alert3 = MagicMock()
        mock_alert3.alert_level = "WARNING"
        mock_alert3.rule_type = "RESOURCE"
        mock_alert3.status = "PENDING"

        result = build_summary_statistics([mock_alert1, mock_alert2, mock_alert3])

        assert result["by_level"]["WARNING"] == 2
        assert result["by_level"]["CRITICAL"] == 1

    def test_counts_by_type(self):
        """测试按类型计数"""
        from app.services.alert_trend_service import build_summary_statistics

        mock_alert1 = MagicMock()
        mock_alert1.alert_level = "WARNING"
        mock_alert1.rule_type = "PROGRESS"
        mock_alert1.status = "PENDING"

        mock_alert2 = MagicMock()
        mock_alert2.alert_level = "WARNING"
        mock_alert2.rule_type = "PROGRESS"
        mock_alert2.status = "PENDING"

        result = build_summary_statistics([mock_alert1, mock_alert2])

        assert result["by_type"]["PROGRESS"] == 2

    def test_counts_by_status(self):
        """测试按状态计数"""
        from app.services.alert_trend_service import build_summary_statistics

        mock_alert1 = MagicMock()
        mock_alert1.alert_level = "WARNING"
        mock_alert1.rule_type = "PROGRESS"
        mock_alert1.status = "PENDING"

        mock_alert2 = MagicMock()
        mock_alert2.alert_level = "WARNING"
        mock_alert2.rule_type = "PROGRESS"
        mock_alert2.status = "RESOLVED"

        mock_alert3 = MagicMock()
        mock_alert3.alert_level = "WARNING"
        mock_alert3.rule_type = "PROGRESS"
        mock_alert3.status = "PENDING"

        result = build_summary_statistics([mock_alert1, mock_alert2, mock_alert3])

        assert result["by_status"]["PENDING"] == 2
        assert result["by_status"]["RESOLVED"] == 1

    def test_handles_unknown_values(self):
        """测试处理未知值"""
        from app.services.alert_trend_service import build_summary_statistics

        mock_alert = MagicMock()
        mock_alert.alert_level = None
        mock_alert.rule_type = None
        mock_alert.status = None

        result = build_summary_statistics([mock_alert])

        assert result["by_level"]["UNKNOWN"] == 1
        assert result["by_type"]["UNKNOWN"] == 1
        assert result["by_status"]["UNKNOWN"] == 1
