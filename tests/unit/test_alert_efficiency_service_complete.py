# -*- coding: utf-8 -*-
"""
Tests for alert_efficiency_service service
"""

from datetime import datetime


class MockAlertRecord:
    def __init__(
        self,
        alert_no: str,
        alert_level: str,
        triggered_at: datetime,
        acknowledged_at: datetime = None,
        status: str = "OPEN",
        is_escalated: bool = False,
        project_id: int = None,
        handler_id: int = None,
        rule=None,
        rule_id: int = None,
        target_type: str = None,
        target_id: int = None,
    ):
        self.alert_no = alert_no
        self.alert_level = alert_level
        self.triggered_at = triggered_at
        self.acknowledged_at = acknowledged_at
        self.status = status
        self.is_escalated = is_escalated
        self.project_id = project_id
        self.handler_id = handler_id
        self.rule = rule
        self.rule_id = rule_id
        self.target_type = target_type
        self.target_id = target_id


class MockAlertRule:
    def __init__(self, rule_type: str):
        self.rule_type = rule_type


class MockAlertRuleEngine:
    RESPONSE_TIMEOUT = {"HINT": 24, "WARNING": 12, "ERROR": 8, "CRITICAL": 4}


class TestCalculateBasicMetrics:
    def test_calculate_basic_metrics_empty(self):
        from app.services.alert_efficiency_service import calculate_basic_metrics

        metrics = calculate_basic_metrics([], MockAlertRuleEngine())

        assert metrics["processing_rate"] == 0
        assert metrics["timely_processing_rate"] == 0
        assert metrics["escalation_rate"] == 0
        assert metrics["duplicate_rate"] == 0

    def test_calculate_basic_metrics_processed(self):
        from app.services.alert_efficiency_service import calculate_basic_metrics

        alerts = [
            MockAlertRecord(
                alert_no="ALT001",
                alert_level="WARNING",
                triggered_at=datetime(2024, 2, 1, 10, 0),
                acknowledged_at=datetime(2024, 2, 1, 11, 0),
                status="RESOLVED",
                is_escalated=False,
            ),
            MockAlertRecord(
                alert_no="ALT002",
                alert_level="ERROR",
                triggered_at=datetime(2024, 2, 1, 12, 0),
                acknowledged_at=datetime(2024, 2, 1, 12, 30),
                status="OPEN",
                is_escalated=False,
            ),
        ]

        metrics = calculate_basic_metrics(alerts, MockAlertRuleEngine())

        assert metrics["processing_rate"] == 0.5
        assert metrics["escalation_rate"] == 0.0

    def test_calculate_basic_metrics_timely(self):
        from app.services.alert_efficiency_service import calculate_basic_metrics

        alerts = [
            MockAlertRecord(
                alert_no="ALT001",
                alert_level="WARNING",
                triggered_at=datetime(2024, 2, 1, 10, 0),
                acknowledged_at=datetime(2024, 2, 1, 11, 0),
                status="RESOLVED",
                is_escalated=False,
            ),
        ]

        metrics = calculate_basic_metrics(alerts, MockAlertRuleEngine())

        assert metrics["timely_processing_rate"] == 1.0

    def test_calculate_basic_metrics_escalated(self):
        from app.services.alert_efficiency_service import calculate_basic_metrics

        alerts = [
            MockAlertRecord(
                alert_no="ALT001",
                alert_level="WARNING",
                triggered_at=datetime(2024, 2, 1, 10, 0),
                acknowledged_at=datetime(2024, 2, 1, 11, 0),
                status="RESOLVED",
                is_escalated=True,
            ),
            MockAlertRecord(
                alert_no="ALT002",
                alert_level="ERROR",
                triggered_at=datetime(2024, 2, 1, 12, 0),
                acknowledged_at=datetime(2024, 2, 1, 12, 30),
                status="OPEN",
                is_escalated=False,
            ),
        ]

        metrics = calculate_basic_metrics(alerts, MockAlertRuleEngine())

        assert metrics["escalation_rate"] == 0.5

    def test_calculate_basic_metrics_duplicate(self):
        from app.services.alert_efficiency_service import calculate_basic_metrics

        alerts = [
            MockAlertRecord(
                alert_no="ALT001",
                alert_level="WARNING",
                triggered_at=datetime(2024, 2, 1, 10, 0),
                acknowledged_at=datetime(2024, 2, 1, 11, 0),
                status="RESOLVED",
                is_escalated=False,
                project_id=1,
                rule_id=1,
                target_type="PROJECT",
                target_id=1,
            ),
            MockAlertRecord(
                alert_no="ALT002",
                alert_level="WARNING",
                triggered_at=datetime(2024, 2, 1, 11, 0),
                acknowledged_at=datetime(2024, 2, 1, 12, 0),
                status="RESOLVED",
                is_escalated=False,
                project_id=1,
                rule_id=1,
                target_type="PROJECT",
                target_id=1,
            ),
        ]

        metrics = calculate_basic_metrics(alerts, MockAlertRuleEngine())

        assert metrics["duplicate_rate"] == 0.5


class TestGenerateRankings:
    def test_generate_rankings_empty(self):
        from app.services.alert_efficiency_service import generate_rankings

        rankings = generate_rankings({}, {})

        assert rankings["best_projects"] == []
        assert rankings["worst_projects"] == []
        assert rankings["best_handlers"] == []
        assert rankings["worst_handlers"] == []

    def test_generate_rankings_projects(self):
        from app.services.alert_efficiency_service import generate_rankings

        project_metrics = {
            "Project A": {
                "project_id": 1,
                "total": 10,
                "processed": 10,
                "timely_processed": 9,
                "escalated": 0,
                "processing_rate": 1.0,
                "timely_processing_rate": 0.9,
                "escalation_rate": 0.0,
                "efficiency_score": 95.0,
            },
            "Project B": {
                "project_id": 2,
                "total": 5,
                "processed": 3,
                "timely_processed": 2,
                "escalated": 1,
                "processing_rate": 0.6,
                "timely_processing_rate": 0.4,
                "escalation_rate": 0.2,
                "efficiency_score": 60.0,
            },
        }

        handler_metrics = {}

        rankings = generate_rankings(project_metrics, handler_metrics)

        assert len(rankings["best_projects"]) >= 1
        assert rankings["best_projects"][0]["project_name"] == "Project A"
        assert rankings["best_projects"][0]["efficiency_score"] == 95.0

        assert len(rankings["worst_projects"]) >= 1
        assert rankings["worst_projects"][0]["project_name"] == "Project B"
        assert rankings["worst_projects"][0]["efficiency_score"] == 60.0

    def test_generate_rankings_handlers(self):
        from app.services.alert_efficiency_service import generate_rankings

        project_metrics = {}

        handler_metrics = {
            "User A": {
                "user_id": 1,
                "total": 8,
                "processed": 8,
                "timely_processed": 8,
                "escalated": 0,
                "processing_rate": 1.0,
                "timely_processing_rate": 1.0,
                "escalation_rate": 0.0,
                "efficiency_score": 100.0,
            },
            "User B": {
                "user_id": 2,
                "total": 6,
                "processed": 4,
                "timely_processed": 3,
                "escalated": 1,
                "processing_rate": 0.67,
                "timely_processing_rate": 0.5,
                "escalation_rate": 0.17,
                "efficiency_score": 70.0,
            },
        }

        rankings = generate_rankings(project_metrics, handler_metrics)

        assert len(rankings["best_handlers"]) >= 1
        assert rankings["best_handlers"][0]["handler_name"] == "User A"
        assert rankings["best_handlers"][0]["efficiency_score"] == 100.0

        assert len(rankings["worst_handlers"]) >= 1
        assert rankings["worst_handlers"][0]["handler_name"] == "User B"
        assert rankings["worst_handlers"][0]["efficiency_score"] == 70.0
