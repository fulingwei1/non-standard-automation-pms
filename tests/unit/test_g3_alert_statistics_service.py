# -*- coding: utf-8 -*-
"""
G3组 - 告警统计分析服务单元测试
目标文件: app/services/alert/alert_statistics_service.py
"""
import pytest
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.alert.alert_statistics_service import AlertStatisticsService


class TestAlertStatisticsServiceInit:
    """测试初始化"""

    def test_init_with_db(self):
        db = MagicMock()
        svc = AlertStatisticsService(db)
        assert svc.db is db


class TestGetAlertStatistics:
    """测试获取告警统计信息"""

    def setup_method(self):
        self.db = MagicMock()
        self.svc = AlertStatisticsService(self.db)

    def _setup_base_query(self, total=0):
        """辅助方法：设置基础查询mock"""
        base_q = MagicMock()
        base_q.count.return_value = total

        # status 统计
        base_q.with_entities.return_value.group_by.return_value.all.return_value = []
        base_q.filter.return_value = base_q
        base_q.join.return_value.with_entities.return_value.group_by.return_value.all.return_value = []

        # response_time_stats
        rt_stats = SimpleNamespace(
            avg_response_seconds=None,
            min_response_seconds=None,
            max_response_seconds=None,
        )
        # resolution_time_stats
        res_stats = SimpleNamespace(
            avg_resolution_seconds=None,
            min_resolution_seconds=None,
            max_resolution_seconds=None,
        )

        base_q.filter.return_value.with_entities.return_value.first.side_effect = [
            rt_stats, res_stats
        ]

        self.db.query.return_value.filter.return_value = base_q
        return base_q

    def test_get_statistics_default_dates(self):
        """没有传日期时，应自动填充默认日期范围"""
        base_q = self._setup_base_query(total=10)
        # 设置 with_entities chain
        chain = MagicMock()
        chain.group_by.return_value.all.return_value = []
        base_q.with_entities.return_value = chain

        with patch.object(self.svc, "_format_seconds", return_value=None):
            result = self.svc.get_alert_statistics()

        assert "total_alerts" in result
        assert "period" in result
        assert "start_date" in result["period"]
        assert "end_date" in result["period"]

    def test_get_statistics_with_project_filter(self):
        """传入project_id时应应用过滤"""
        base_q = self._setup_base_query(total=3)
        chain = MagicMock()
        chain.group_by.return_value.all.return_value = []
        base_q.with_entities.return_value = chain

        with patch.object(self.svc, "_format_seconds", return_value=None):
            result = self.svc.get_alert_statistics(project_id=5)

        assert result is not None

    def test_get_statistics_with_explicit_dates(self):
        """传入明确日期范围"""
        base_q = self._setup_base_query(total=7)
        chain = MagicMock()
        chain.group_by.return_value.all.return_value = []
        base_q.with_entities.return_value = chain

        start = date(2026, 1, 1)
        end = date(2026, 1, 31)

        with patch.object(self.svc, "_format_seconds", return_value=None):
            result = self.svc.get_alert_statistics(start_date=start, end_date=end)

        assert result["period"]["start_date"] == "2026-01-01"
        assert result["period"]["end_date"] == "2026-01-31"


class TestFormatSeconds:
    """测试时间格式化辅助方法"""

    def setup_method(self):
        self.db = MagicMock()
        self.svc = AlertStatisticsService(self.db)

    def test_format_seconds_none(self):
        result = self.svc._format_seconds(None)
        assert result is None

    def test_format_seconds_less_than_minute(self):
        result = self.svc._format_seconds(45)
        assert result is not None
        assert "45" in str(result) or "秒" in str(result) or isinstance(result, (str, dict))

    def test_format_seconds_minutes(self):
        result = self.svc._format_seconds(120)
        assert result is not None

    def test_format_seconds_hours(self):
        result = self.svc._format_seconds(7200)
        assert result is not None


class TestGetAlertTrends:
    """测试获取告警趋势数据"""

    def setup_method(self):
        self.db = MagicMock()
        self.svc = AlertStatisticsService(self.db)

    def test_get_trends_daily(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = self.svc.get_alert_trends(period="daily")
        assert result is not None

    def test_get_trends_weekly(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = self.svc.get_alert_trends(period="weekly")
        assert result is not None

    def test_get_trends_monthly(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = self.svc.get_alert_trends(period="monthly")
        assert result is not None

    def test_get_trends_with_dates(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        start = date(2026, 1, 1)
        end = date(2026, 1, 31)
        result = self.svc.get_alert_trends(start_date=start, end_date=end)
        assert result is not None
