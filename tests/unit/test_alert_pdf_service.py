# -*- coding: utf-8 -*-
"""Tests for alert_pdf_service.py"""
from unittest.mock import MagicMock, patch
from datetime import date, datetime

from app.services.alert_pdf_service import (
    build_alert_query,
    calculate_alert_statistics,
)


class TestBuildAlertQuery:
    def test_no_filters(self):
        db = MagicMock()
        result = build_alert_query(db)
        assert result is not None  # returns query object

    def test_with_all_filters(self):
        db = MagicMock()
        result = build_alert_query(
            db, project_id=1, alert_level="HIGH", status="PENDING",
            rule_type="THRESHOLD", start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )
        assert result is not None


class TestCalculateAlertStatistics:
    def test_empty(self):
        result = calculate_alert_statistics([])
        assert result['total'] == 0
        assert result['by_level'] == {}

    def test_with_alerts(self):
        a1 = MagicMock(alert_level="HIGH", status="PENDING", rule=MagicMock(rule_type="THRESHOLD"))
        a2 = MagicMock(alert_level="LOW", status="RESOLVED", rule=MagicMock(rule_type="OVERDUE"))
        a3 = MagicMock(alert_level="HIGH", status="PENDING", rule=None)
        result = calculate_alert_statistics([a1, a2, a3])
        assert result['total'] == 3
        assert result['by_level']['HIGH'] == 2
        assert result['by_level']['LOW'] == 1
        assert result['by_status']['PENDING'] == 2
        assert result['by_type']['THRESHOLD'] == 1
        assert result['by_type']['UNKNOWN'] == 1
