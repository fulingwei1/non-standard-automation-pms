# -*- coding: utf-8 -*-
"""Tests for alert_efficiency_service.py"""
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from app.services.alert_efficiency_service import (
    calculate_basic_metrics,
    calculate_project_metrics,
    calculate_handler_metrics,
    calculate_type_metrics,
    generate_rankings,
)


def _make_alert(status="RESOLVED", level="HIGH", is_escalated=False,
                triggered_at=None, acknowledged_at=None, rule_id=1,
                target_type="SHORTAGE", target_id=1, project_id=1,
                handler_id=1):
    a = MagicMock()
    a.status = status
    a.alert_level = level
    a.is_escalated = is_escalated
    a.triggered_at = triggered_at or datetime(2025, 1, 1, 8, 0)
    a.acknowledged_at = acknowledged_at or datetime(2025, 1, 1, 9, 0)
    a.rule_id = rule_id
    a.target_type = target_type
    a.target_id = target_id
    a.project_id = project_id
    a.handler_id = handler_id
    a.acknowledged_by = handler_id
    a.rule = MagicMock(rule_type="THRESHOLD")
    return a


class TestCalculateBasicMetrics:
    def test_empty(self):
        engine = MagicMock()
        result = calculate_basic_metrics([], engine)
        assert result['processing_rate'] == 0

    def test_all_resolved(self):
        engine = MagicMock()
        engine.RESPONSE_TIMEOUT = {"HIGH": 8}
        alerts = [_make_alert() for _ in range(3)]
        result = calculate_basic_metrics(alerts, engine)
        assert result['processing_rate'] == 1.0
        assert result['timely_processing_rate'] == 1.0

    def test_escalated(self):
        engine = MagicMock()
        engine.RESPONSE_TIMEOUT = {"HIGH": 8}
        alerts = [_make_alert(is_escalated=True)]
        result = calculate_basic_metrics(alerts, engine)
        assert result['escalation_rate'] == 1.0

    def test_duplicate_detection(self):
        engine = MagicMock()
        engine.RESPONSE_TIMEOUT = {"HIGH": 8}
        a1 = _make_alert(triggered_at=datetime(2025, 1, 1, 8, 0))
        a2 = _make_alert(triggered_at=datetime(2025, 1, 1, 10, 0))  # same rule/target within 24h
        result = calculate_basic_metrics([a1, a2], engine)
        assert result['duplicate_rate'] == 0.5


class TestCalculateProjectMetrics:
    def test_basic(self):
        db = MagicMock()
        engine = MagicMock()
        engine.RESPONSE_TIMEOUT = {"HIGH": 8}
        project = MagicMock(project_name="项目A")
        db.query.return_value.filter.return_value.first.return_value = project
        alerts = [_make_alert()]
        result = calculate_project_metrics(alerts, db, engine)
        assert '项目A' in result


class TestCalculateTypeMetrics:
    def test_basic(self):
        engine = MagicMock()
        engine.RESPONSE_TIMEOUT = {"HIGH": 8}
        alerts = [_make_alert()]
        result = calculate_type_metrics(alerts, engine)
        assert 'THRESHOLD' in result


class TestGenerateRankings:
    def test_empty(self):
        result = generate_rankings({}, {})
        assert result['best_projects'] == []

    def test_with_data(self):
        pm = {f'P{i}': {'project_id': i, 'total': 10, 'efficiency_score': 80 + i,
                         'processing_rate': 0.9, 'timely_processing_rate': 0.8}
              for i in range(6)}
        hm = {f'H{i}': {'user_id': i, 'total': 10, 'efficiency_score': 70 + i,
                         'processing_rate': 0.8, 'timely_processing_rate': 0.7}
              for i in range(6)}
        result = generate_rankings(pm, hm)
        assert len(result['best_projects']) <= 5
