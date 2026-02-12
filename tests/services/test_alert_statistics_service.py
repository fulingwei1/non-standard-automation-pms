# -*- coding: utf-8 -*-
"""AlertStatisticsService 单元测试"""

import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, PropertyMock

# Patch missing model attributes before importing
from app.models.alert import AlertRecord
for _attr in ('resolved_at', 'assigned_user', 'title'):
    if not hasattr(AlertRecord, _attr):
        setattr(AlertRecord, _attr, MagicMock())

from app.services.alert.alert_statistics_service import AlertStatisticsService


class TestAlertStatisticsService(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.service = AlertStatisticsService(self.db)

    # --- _format_seconds ---
    def test_format_seconds_none(self):
        self.assertIsNone(self.service._format_seconds(None))

    def test_format_seconds_zero(self):
        self.assertIsNone(self.service._format_seconds(0))

    def test_format_seconds_minutes_only(self):
        self.assertEqual(self.service._format_seconds(300), "5分钟")

    def test_format_seconds_hours_and_minutes(self):
        self.assertEqual(self.service._format_seconds(3720), "1小时2分钟")

    # --- _get_percentile ---
    def test_get_percentile_empty(self):
        self.assertEqual(self.service._get_percentile([], 50), 0)

    def test_get_percentile_single(self):
        self.assertEqual(self.service._get_percentile([10.0], 50), 10.0)

    def test_get_percentile_normal(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        self.assertEqual(self.service._get_percentile(data, 50), 6.0)
        self.assertEqual(self.service._get_percentile(data, 90), 10.0)

    # --- get_alert_statistics ---
    @patch("app.services.alert.alert_statistics_service.joinedload", return_value=MagicMock())
    def test_get_alert_statistics_returns_structure(self, _jl):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = []
        mock_first = MagicMock()
        mock_first.avg_response_seconds = 600
        mock_first.min_response_seconds = 60
        mock_first.max_response_seconds = 3600
        mock_first.avg_resolution_seconds = 7200
        mock_first.min_resolution_seconds = 1800
        mock_first.max_resolution_seconds = 14400
        mock_query.first.return_value = mock_first

        result = self.service.get_alert_statistics(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            project_id=1
        )

        self.assertIn("total_alerts", result)
        self.assertEqual(result["total_alerts"], 5)
        self.assertIn("response_metrics", result)

    @patch("app.services.alert.alert_statistics_service.joinedload", return_value=MagicMock())
    def test_get_alert_statistics_defaults_dates(self, _jl):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.first.return_value = None

        result = self.service.get_alert_statistics()
        self.assertEqual(result["total_alerts"], 0)

    # --- get_alert_trends ---
    def test_get_alert_trends(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service.get_alert_trends(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            period="daily"
        )
        self.assertIn("trend_data", result)
        self.assertEqual(result["period"]["granularity"], "daily")

    def test_get_alert_trends_with_data(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        item = MagicMock()
        item.period = date(2025, 1, 1)
        item.status = "pending"
        item.count = 3
        mock_query.all.return_value = [item]

        result = self.service.get_alert_trends(
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
        self.assertIn("2025-01-01", result["trend_data"])

    # --- get_response_metrics ---
    def test_get_response_metrics_empty(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service.get_response_metrics(
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
        self.assertEqual(result["total_responded"], 0)

    def test_get_response_metrics_with_data(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        alert1 = MagicMock()
        alert1.acknowledged_at = datetime(2025, 1, 1, 1, 0, 0)
        alert1.created_at = datetime(2025, 1, 1, 0, 0, 0)
        alert2 = MagicMock()
        alert2.acknowledged_at = datetime(2025, 1, 2, 2, 0, 0)
        alert2.created_at = datetime(2025, 1, 2, 0, 0, 0)
        mock_query.all.return_value = [alert1, alert2]

        result = self.service.get_response_metrics(
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
        self.assertEqual(result["total_responded"], 2)
        self.assertIn("within_4hours", result["response_time_distribution"])

    # --- get_alert_dashboard_data ---
    @patch("app.services.alert.alert_statistics_service.joinedload", return_value=MagicMock())
    def test_get_alert_dashboard_data(self, _jl):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.scalar.return_value = None

        result = self.service.get_alert_dashboard_data(project_id=1)
        self.assertIn("today_summary", result)
        self.assertIn("week_trend", result)
        self.assertIn("critical_alerts", result)

    # --- get_efficiency_metrics ---
    def test_get_efficiency_metrics(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.with_entities.return_value = mock_query
        mock_query.scalar.return_value = 300.0

        result = self.service.get_efficiency_metrics(
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
        self.assertIn("resolution_rate", result)
        self.assertIn("total_processed", result)


if __name__ == "__main__":
    unittest.main()
