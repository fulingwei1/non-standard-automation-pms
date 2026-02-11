# -*- coding: utf-8 -*-
"""Tests for alert_response_service.py"""
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from app.services.alert_response_service import (
    calculate_response_times,
    calculate_resolve_times,
    calculate_response_distribution,
    calculate_level_metrics,
    calculate_type_metrics,
    calculate_project_metrics,
    calculate_handler_metrics,
    generate_response_rankings,
)


class TestCalculateResponseTimes:
    def test_valid_alerts(self):
        alert = MagicMock()
        alert.triggered_at = datetime(2025, 1, 1, 8, 0)
        alert.acknowledged_at = datetime(2025, 1, 1, 10, 0)
        result = calculate_response_times([alert])
        assert len(result) == 1
        assert result[0]['minutes'] == 120.0
        assert result[0]['hours'] == 2.0

    def test_missing_timestamps(self):
        alert = MagicMock(triggered_at=None, acknowledged_at=None)
        assert calculate_response_times([alert]) == []

    def test_empty_list(self):
        assert calculate_response_times([]) == []


class TestCalculateResolveTimes:
    def test_valid(self):
        alert = MagicMock()
        alert.acknowledged_at = datetime(2025, 1, 1, 8, 0)
        alert.handle_end_at = datetime(2025, 1, 1, 12, 0)
        result = calculate_resolve_times([alert])
        assert len(result) == 1
        assert result[0]['hours'] == 4.0

    def test_missing_timestamps(self):
        alert = MagicMock(acknowledged_at=None, handle_end_at=None)
        assert calculate_resolve_times([alert]) == []


class TestCalculateResponseDistribution:
    def test_distribution_buckets(self):
        times = [
            {'hours': 0.5},
            {'hours': 2.0},
            {'hours': 6.0},
            {'hours': 10.0},
        ]
        result = calculate_response_distribution(times)
        assert result['<1小时'] == 1
        assert result['1-4小时'] == 1
        assert result['4-8小时'] == 1
        assert result['>8小时'] == 1

    def test_empty(self):
        result = calculate_response_distribution([])
        assert all(v == 0 for v in result.values())


class TestCalculateLevelMetrics:
    def test_groups_by_level(self):
        alert1 = MagicMock(alert_level="HIGH")
        alert2 = MagicMock(alert_level="HIGH")
        alert3 = MagicMock(alert_level="LOW")
        times = [
            {'alert': alert1, 'hours': 1.0},
            {'alert': alert2, 'hours': 3.0},
            {'alert': alert3, 'hours': 2.0},
        ]
        result = calculate_level_metrics(times)
        assert result['HIGH']['count'] == 2
        assert result['HIGH']['avg_hours'] == 2.0
        assert result['LOW']['count'] == 1


class TestCalculateTypeMetrics:
    def test_groups_by_rule_type(self):
        rule = MagicMock(rule_type="THRESHOLD")
        alert = MagicMock(rule=rule)
        times = [{'alert': alert, 'hours': 3.0}]
        result = calculate_type_metrics(times)
        assert 'THRESHOLD' in result
        assert result['THRESHOLD']['count'] == 1

    def test_no_rule(self):
        alert = MagicMock(rule=None)
        times = [{'alert': alert, 'hours': 1.0}]
        result = calculate_type_metrics(times)
        assert 'UNKNOWN' in result


class TestCalculateProjectMetrics:
    def test_groups_by_project(self):
        db = MagicMock()
        project = MagicMock(project_name="项目A")
        db.query.return_value.filter.return_value.first.return_value = project
        alert = MagicMock(project_id=1, acknowledged_by=1)
        times = [{'alert': alert, 'hours': 2.0}]
        result = calculate_project_metrics(times, db)
        assert '项目A' in result

    def test_no_project_id(self):
        db = MagicMock()
        alert = MagicMock(project_id=None)
        times = [{'alert': alert, 'hours': 1.0}]
        result = calculate_project_metrics(times, db)
        assert result == {}


class TestGenerateResponseRankings:
    def test_rankings(self):
        project_metrics = {
            'P1': {'project_id': 1, 'avg_hours': 1.0, 'count': 5},
            'P2': {'project_id': 2, 'avg_hours': 5.0, 'count': 3},
        }
        handler_metrics = {
            'H1': {'user_id': 1, 'avg_hours': 0.5, 'count': 10},
            'H2': {'user_id': 2, 'avg_hours': 8.0, 'count': 2},
        }
        result = generate_response_rankings(project_metrics, handler_metrics)
        assert len(result['fastest_projects']) > 0
        assert result['fastest_projects'][0]['project_name'] == 'P1'
        assert result['fastest_handlers'][0]['handler_name'] == 'H1'
