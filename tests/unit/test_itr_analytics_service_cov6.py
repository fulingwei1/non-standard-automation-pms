# -*- coding: utf-8 -*-
"""
第六批覆盖测试 - itr_analytics_service.py
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

try:
    from app.services.itr_analytics_service import (
        analyze_resolution_time,
        analyze_satisfaction_trend,
        identify_bottlenecks,
        analyze_sla_performance,
    )
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="itr_analytics_service not importable")


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.all.return_value = []
    return db


class TestAnalyzeResolutionTime:
    def test_no_tickets(self, mock_db):
        result = analyze_resolution_time(mock_db)
        assert isinstance(result, dict)
        assert result.get("total_tickets") == 0

    def test_with_date_filter(self, mock_db):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        result = analyze_resolution_time(mock_db, start_date=start, end_date=end)
        assert isinstance(result, dict)

    def test_with_project_filter(self, mock_db):
        result = analyze_resolution_time(mock_db, project_id=1)
        assert isinstance(result, dict)

    def test_with_tickets(self, mock_db):
        ticket = MagicMock()
        ticket.id = 1
        ticket.ticket_no = "TKT-001"
        ticket.problem_type = "BUG"
        ticket.urgency = "HIGH"
        ticket.reported_time = datetime(2024, 1, 1, 9, 0)
        ticket.resolved_time = datetime(2024, 1, 1, 17, 0)
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [ticket]
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [ticket]
        mock_db.query.return_value.filter.return_value.all.return_value = [ticket]
        result = analyze_resolution_time(mock_db)
        assert isinstance(result, dict)


class TestAnalyzeSatisfactionTrend:
    def test_no_satisfaction_data(self, mock_db):
        result = analyze_satisfaction_trend(mock_db)
        assert isinstance(result, dict)

    def test_with_date_range(self, mock_db):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 6, 30)
        result = analyze_satisfaction_trend(mock_db, start_date=start, end_date=end)
        assert isinstance(result, dict)

    def test_with_project_filter(self, mock_db):
        result = analyze_satisfaction_trend(mock_db, project_id=5)
        assert isinstance(result, dict)


class TestIdentifyBottlenecks:
    def test_no_data(self, mock_db):
        result = identify_bottlenecks(mock_db)
        assert isinstance(result, dict)

    def test_with_date_filters(self, mock_db):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        result = identify_bottlenecks(mock_db, start_date=start, end_date=end)
        assert isinstance(result, dict)


class TestAnalyzeSLAPerformance:
    def test_no_sla_records(self, mock_db):
        result = analyze_sla_performance(mock_db)
        assert isinstance(result, dict)

    def test_with_date_range(self, mock_db):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        result = analyze_sla_performance(mock_db, start_date=start, end_date=end)
        assert isinstance(result, dict)

    def test_with_policy_filter(self, mock_db):
        result = analyze_sla_performance(mock_db, policy_id=2)
        assert isinstance(result, dict)

    def test_returns_required_keys(self, mock_db):
        result = analyze_sla_performance(mock_db)
        assert "total_monitors" in result
