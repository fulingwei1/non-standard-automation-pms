# -*- coding: utf-8 -*-
"""
Tests for alert_trend_service service
Covers: app/services/alert_trend_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 71 lines
Batch: 2
"""

from datetime import datetime, date


# Mock AlertRecord for testing
class MockAlertRecord:
    """模拟 AlertRecord 类"""

    def __init__(
        self,
        alert_no: str,
        alert_level: str,
        alert_title: str,
        triggered_at: datetime,
        status: str,
        rule_type: str,
        rule: object = None,
    ):
        self.alert_no = alert_no
        self.alert_level = alert_level
        self.alert_title = alert_title
        self.triggered_at = triggered_at
        self.status = status
        self.rule_type = rule_type
        self.rule = rule


class MockAlertRule:
    """模拟 AlertRule 类"""

    def __init__(self, rule_type: str):
        self.rule_type = rule_type


class TestGetPeriodKey:
    """测试 get_period_key 函数"""

    def test_get_period_key_daily(self):
        """测试按日分组键"""
        from app.services.alert_trend_service import get_period_key

        dt = datetime(2024, 2, 10, 15, 30, 0)
        key = get_period_key(dt, "DAILY")
        assert key == "2024-02-10"

    def test_get_period_key_weekly(self):
        """测试按周分组键"""
        from app.services.alert_trend_service import get_period_key

        # 2024-02-10 是周六，周一是 2024-02-05
        dt = datetime(2024, 2, 10, 15, 30, 0)
        key = get_period_key(dt, "WEEKLY")
        assert key == "2024-02-05"

    def test_get_period_key_monthly(self):
        """测试按月分组键"""
        from app.services.alert_trend_service import get_period_key

        dt = datetime(2024, 2, 10, 15, 30, 0)
        key = get_period_key(dt, "MONTHLY")
        assert key == "2024-02-01"

    def test_get_period_key_unknown_period(self):
        """测试未知周期返回日期"""
        from app.services.alert_trend_service import get_period_key

        dt = datetime(2024, 2, 10, 15, 30, 0)
        key = get_period_key(dt, "UNKNOWN")
        assert key == "2024-02-10"


class TestGenerateDateRange:
    """测试 generate_date_range 函数"""

    def test_generate_date_range_daily(self):
        """测试生成每日日期范围"""
        from app.services.alert_trend_service import generate_date_range

        start = date(2024, 2, 1)
        end = date(2024, 2, 5)
        dates = generate_date_range(start, end, "DAILY")
        assert dates == [
        "2024-02-01",
        "2024-02-02",
        "2024-02-03",
        "2024-02-04",
        "2024-02-05",
        ]

    def test_generate_date_range_monthly(self):
        """测试生成每月日期范围"""
        from app.services.alert_trend_service import generate_date_range

        start = date(2024, 1, 15)
        end = date(2024, 4, 10)
        dates = generate_date_range(start, end, "MONTHLY")
        assert dates == [
        "2024-01-01",
        "2024-02-01",
        "2024-03-01",
        "2024-04-01",
        ]

    def test_generate_date_range_single_day(self):
        """测试生成单日范围"""
        from app.services.alert_trend_service import generate_date_range

        start = date(2024, 2, 1)
        end = date(2024, 2, 1)
        dates = generate_date_range(start, end, "DAILY")
        assert dates == ["2024-02-01"]


class TestBuildTrendStatistics:
    """测试 build_trend_statistics 函数"""

    def test_build_trend_statistics_daily(self):
        """测试构建每日趋势统计"""
        from app.services.alert_trend_service import build_trend_statistics

        alerts = [
        MockAlertRecord(
        alert_no="ALT001",
        alert_level="WARNING",
        alert_title="进度延迟",
        triggered_at=datetime(2024, 2, 1, 10, 0),
        status="RESOLVED",
        rule_type="PROGRESS",
        rule=MockAlertRule("PROGRESS"),
        ),
        MockAlertRecord(
        alert_no="ALT002",
        alert_level="ERROR",
        alert_title="成本超支",
        triggered_at=datetime(2024, 2, 1, 14, 0),
        status="OPEN",
        rule_type="COST",
        rule=MockAlertRule("COST"),
        ),
        MockAlertRecord(
        alert_no="ALT003",
        alert_level="WARNING",
        alert_title="质量异常",
        triggered_at=datetime(2024, 2, 2, 9, 0),
        status="RESOLVED",
        rule_type="QUALITY",
        rule=MockAlertRule("QUALITY"),
        ),
        ]

        stats = build_trend_statistics(alerts, "DAILY")

        assert "date_trends" in stats
        assert "level_trends" in stats
        assert "type_trends" in stats
        assert "status_trends" in stats

        assert stats["date_trends"]["2024-02-01"] == 2
        assert stats["date_trends"]["2024-02-02"] == 1

        assert stats["level_trends"]["2024-02-01"]["WARNING"] == 1
        assert stats["level_trends"]["2024-02-01"]["ERROR"] == 1

    def test_build_trend_statistics_with_null_triggered_at(self):
        """测试忽略未触发的预警"""
        from app.services.alert_trend_service import build_trend_statistics

        alerts = [
        MockAlertRecord(
        alert_no="ALT001",
        alert_level="WARNING",
        alert_title="进度延迟",
        triggered_at=None,
        status="OPEN",
        rule_type="PROGRESS",
        rule=MockAlertRule("PROGRESS"),
        ),
        MockAlertRecord(
        alert_no="ALT002",
        alert_level="ERROR",
        alert_title="成本超支",
        triggered_at=datetime(2024, 2, 1, 14, 0),
        status="OPEN",
        rule_type="COST",
        rule=MockAlertRule("COST"),
        ),
        ]

        stats = build_trend_statistics(alerts, "DAILY")
        assert stats["date_trends"]["2024-02-01"] == 1


class TestBuildSummaryStatistics:
    """测试 build_summary_statistics 函数"""

    def test_build_summary_statistics(self):
        """测试构建汇总统计"""
        from app.services.alert_trend_service import build_summary_statistics

        alerts = [
        MockAlertRecord(
        alert_no="ALT001",
        alert_level="WARNING",
        alert_title="进度延迟",
        triggered_at=datetime(2024, 2, 1, 10, 0),
        status="RESOLVED",
        rule_type="PROGRESS",
        rule=MockAlertRule("PROGRESS"),
        ),
        MockAlertRecord(
        alert_no="ALT002",
        alert_level="ERROR",
        alert_title="成本超支",
        triggered_at=datetime(2024, 2, 1, 14, 0),
        status="OPEN",
        rule_type="COST",
        rule=MockAlertRule("COST"),
        ),
        ]

        stats = build_summary_statistics(alerts)

        assert "by_level" in stats
        assert "by_type" in stats
        assert "by_status" in stats

        assert stats["by_level"]["WARNING"] == 1
        assert stats["by_level"]["ERROR"] == 1

        assert stats["by_type"]["PROGRESS"] == 1
        assert stats["by_type"]["COST"] == 1

        assert stats["by_status"]["RESOLVED"] == 1
        assert stats["by_status"]["OPEN"] == 1

    def test_build_summary_statistics_with_nulls(self):
        """测试处理空值"""
        from app.services.alert_trend_service import build_summary_statistics

        alerts = [
        MockAlertRecord(
        alert_no="ALT001",
        alert_level="WARNING",
        alert_title="进度延迟",
        triggered_at=datetime(2024, 2, 1, 10, 0),
        status="OPEN",
        rule_type="PROGRESS",
        rule=MockAlertRule("PROGRESS"),
        ),
        MockAlertRecord(
        alert_no="ALT002",
        alert_level=None,
        alert_title="成本超支",
        triggered_at=datetime(2024, 2, 1, 14, 0),
        status=None,
        rule_type=None,
        rule=None,
        ),
        ]

        stats = build_summary_statistics(alerts)

        assert stats["by_level"]["WARNING"] == 1
        assert stats["by_level"]["UNKNOWN"] == 1

        assert stats["by_type"]["PROGRESS"] == 1
        assert stats["by_type"]["UNKNOWN"] == 1

        assert stats["by_status"]["OPEN"] == 1
        assert stats["by_status"]["UNKNOWN"] == 1

    def test_build_summary_statistics_empty(self):
        """测试空列表"""
        from app.services.alert_trend_service import build_summary_statistics

        stats = build_summary_statistics([])

        assert stats == {"by_level": {}, "by_type": {}, "by_status": {}}
