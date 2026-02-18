# -*- coding: utf-8 -*-
"""
预警处理效率分析服务单元测试
覆盖: app/services/alert_efficiency_service.py
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest


def make_alert(
    status="PENDING",
    alert_level="level2",
    is_escalated=False,
    triggered_at=None,
    acknowledged_at=None,
    rule_id=1,
    target_type="PROJECT",
    target_id=1,
    project_id=None,
    handler_id=None,
    acknowledged_by=None,
):
    a = MagicMock()
    a.status = status
    a.alert_level = alert_level
    a.is_escalated = is_escalated
    a.triggered_at = triggered_at
    a.acknowledged_at = acknowledged_at
    a.rule_id = rule_id
    a.target_type = target_type
    a.target_id = target_id
    a.project_id = project_id
    a.handler_id = handler_id
    a.acknowledged_by = acknowledged_by
    return a


@pytest.fixture
def mock_engine():
    engine = MagicMock()
    engine.RESPONSE_TIMEOUT = {"level1": 1, "level2": 4, "level3": 8, "level4": 24}
    return engine


# ─── calculate_basic_metrics ─────────────────────────────────────────────────

class TestCalculateBasicMetrics:
    def test_empty_list_returns_zeros(self, mock_engine):
        from app.services.alert_efficiency_service import calculate_basic_metrics
        result = calculate_basic_metrics([], mock_engine)
        assert result["processing_rate"] == 0
        assert result["timely_processing_rate"] == 0
        assert result["escalation_rate"] == 0
        assert result["duplicate_rate"] == 0

    def test_all_resolved(self, mock_engine):
        from app.services.alert_efficiency_service import calculate_basic_metrics
        now = datetime.now()
        alerts = [
            make_alert(status="RESOLVED", triggered_at=now - timedelta(hours=2), acknowledged_at=now - timedelta(hours=1)),
            make_alert(status="CLOSED", triggered_at=now - timedelta(hours=5), acknowledged_at=now - timedelta(hours=4)),
        ]
        result = calculate_basic_metrics(alerts, mock_engine)
        assert result["processing_rate"] == 1.0

    def test_none_resolved(self, mock_engine):
        from app.services.alert_efficiency_service import calculate_basic_metrics
        alerts = [make_alert(status="PENDING"), make_alert(status="PROCESSING")]
        result = calculate_basic_metrics(alerts, mock_engine)
        assert result["processing_rate"] == 0.0

    def test_escalation_rate(self, mock_engine):
        from app.services.alert_efficiency_service import calculate_basic_metrics
        alerts = [
            make_alert(is_escalated=True),
            make_alert(is_escalated=True),
            make_alert(is_escalated=False),
            make_alert(is_escalated=False),
        ]
        result = calculate_basic_metrics(alerts, mock_engine)
        assert result["escalation_rate"] == 0.5

    def test_duplicate_rate(self, mock_engine):
        """同一规则+目标在24小时内重复触发，计入重复"""
        from app.services.alert_efficiency_service import calculate_basic_metrics
        now = datetime.now()
        a1 = make_alert(triggered_at=now - timedelta(hours=2), rule_id=1, target_type="PROJECT", target_id=1)
        a2 = make_alert(triggered_at=now - timedelta(hours=1), rule_id=1, target_type="PROJECT", target_id=1)
        a3 = make_alert(triggered_at=now, rule_id=2, target_type="PROJECT", target_id=1)  # different rule

        result = calculate_basic_metrics([a1, a2, a3], mock_engine)
        # a2 is duplicate of a1 → duplicate_count=1, total=3 → 1/3
        assert result["duplicate_rate"] == pytest.approx(1 / 3)

    def test_timely_processing_rate(self, mock_engine):
        """在响应时限内处理的比率"""
        from app.services.alert_efficiency_service import calculate_basic_metrics
        now = datetime.now()
        # level2: timeout=4h, resolved in 2h (timely)
        a1 = make_alert(status="RESOLVED", alert_level="level2",
                        triggered_at=now - timedelta(hours=3),
                        acknowledged_at=now - timedelta(hours=1))  # 2h response
        # level1: timeout=1h, resolved in 3h (not timely)
        a2 = make_alert(status="RESOLVED", alert_level="level1",
                        triggered_at=now - timedelta(hours=4),
                        acknowledged_at=now - timedelta(hours=1))  # 3h response

        result = calculate_basic_metrics([a1, a2], mock_engine)
        # Only a1 is timely, total=2 → timely_rate = 0.5
        assert result["timely_processing_rate"] == pytest.approx(0.5)

    def test_mixed_alert_statuses(self, mock_engine):
        from app.services.alert_efficiency_service import calculate_basic_metrics
        alerts = [
            make_alert(status="RESOLVED"),
            make_alert(status="CLOSED"),
            make_alert(status="PENDING"),
            make_alert(status="PROCESSING"),
        ]
        result = calculate_basic_metrics(alerts, mock_engine)
        assert result["processing_rate"] == pytest.approx(0.5)


# ─── calculate_project_metrics ───────────────────────────────────────────────

class TestCalculateProjectMetrics:
    def test_no_project_alerts_returns_empty(self, mock_engine):
        from app.services.alert_efficiency_service import calculate_project_metrics
        alerts = [make_alert(project_id=None)]
        mock_db = MagicMock()
        result = calculate_project_metrics(alerts, mock_db, mock_engine)
        assert result == {}

    def test_groups_by_project(self, mock_engine):
        from app.services.alert_efficiency_service import calculate_project_metrics

        mock_project = MagicMock()
        mock_project.project_name = "项目A"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        alerts = [
            make_alert(status="RESOLVED", project_id=1),
            make_alert(status="PENDING", project_id=1),
        ]
        result = calculate_project_metrics(alerts, mock_db, mock_engine)
        assert "项目A" in result
        assert result["项目A"]["total"] == 2
        assert result["项目A"]["processing_rate"] == 0.5


# ─── calculate_type_metrics ──────────────────────────────────────────────────

class TestCalculateTypeMetrics:
    def test_groups_by_rule_type(self, mock_engine):
        from app.services.alert_efficiency_service import calculate_type_metrics

        a1 = make_alert(status="RESOLVED")
        a1.rule = MagicMock()
        a1.rule.rule_type = "COST"

        a2 = make_alert(status="PENDING")
        a2.rule = MagicMock()
        a2.rule.rule_type = "SCHEDULE"

        a3 = make_alert(status="RESOLVED")
        a3.rule = MagicMock()
        a3.rule.rule_type = "COST"

        result = calculate_type_metrics([a1, a2, a3], mock_engine)
        assert "COST" in result
        assert "SCHEDULE" in result
        assert result["COST"]["total"] == 2
        assert result["COST"]["processing_rate"] == 1.0
        assert result["SCHEDULE"]["processing_rate"] == 0.0

    def test_no_rule_shows_unknown(self, mock_engine):
        from app.services.alert_efficiency_service import calculate_type_metrics

        a1 = make_alert(status="PENDING")
        a1.rule = None

        result = calculate_type_metrics([a1], mock_engine)
        assert "UNKNOWN" in result


# ─── generate_rankings ────────────────────────────────────────────────────────

class TestGenerateRankings:
    def test_filters_projects_with_few_alerts(self):
        """少于5个预警的项目不进入排行榜"""
        from app.services.alert_efficiency_service import generate_rankings

        project_metrics = {
            "小项目": {"project_id": 1, "total": 3, "efficiency_score": 90,
                       "processing_rate": 0.9, "timely_processing_rate": 0.8},
        }
        handler_metrics = {}
        result = generate_rankings(project_metrics, handler_metrics)
        assert result["best_projects"] == []
        assert result["worst_projects"] == []

    def test_ranks_by_efficiency_score(self):
        """按效率得分正确排序"""
        from app.services.alert_efficiency_service import generate_rankings

        project_metrics = {
            f"项目{i}": {
                "project_id": i, "total": 10,
                "efficiency_score": 100 - i * 10,
                "processing_rate": 1.0,
                "timely_processing_rate": 0.9,
            }
            for i in range(1, 7)
        }
        handler_metrics = {}
        result = generate_rankings(project_metrics, handler_metrics)
        # Best first should be 项目1 (score=90)
        assert result["best_projects"][0]["project_name"] == "项目1"
        # Worst first should be 项目6 (score=40)
        assert result["worst_projects"][0]["project_name"] == "项目6"
