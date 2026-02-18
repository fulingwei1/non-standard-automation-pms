# -*- coding: utf-8 -*-
"""第二十一批：预警升级服务单元测试"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta
import json

pytest.importorskip("app.services.alert_escalation_service")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    from app.services.alert_escalation_service import AlertEscalationService
    return AlertEscalationService(mock_db)


def _make_alert(alert_id=1, level="WARN", status="PENDING", triggered_hours_ago=30):
    a = MagicMock()
    a.id = alert_id
    a.alert_no = f"ALT-{alert_id:04d}"
    a.alert_title = "测试预警"
    a.alert_content = "预警内容" * 10
    a.alert_level = level
    a.status = status
    a.triggered_at = datetime.now() - timedelta(hours=triggered_hours_ago)
    a.alert_data = None
    a.handler_id = None
    a.escalated_to = None
    a.acknowledged_by = None
    a.created_by = 1
    a.updated_by = None
    a.project = None
    a.project_id = None
    a.target_type = "PROJECT"
    a.target_name = "项目A"
    return a


class TestEscalationPath:
    def test_escalation_path_defined(self, service):
        assert "INFO" in service.ESCALATION_PATH
        assert "WARN" in service.ESCALATION_PATH
        assert service.ESCALATION_PATH["WARN"] == "HIGH"
        assert service.ESCALATION_PATH["HIGH"] == "CRITICAL"

    def test_escalation_timeout_defined(self, service):
        assert "INFO" in service.ESCALATION_TIMEOUT
        assert service.ESCALATION_TIMEOUT["HIGH"] == 12


class TestShouldEscalate:
    def test_should_escalate_when_overdue(self, service):
        alert = _make_alert(level="WARN", triggered_hours_ago=48)
        assert service._should_escalate(alert) is True

    def test_should_not_escalate_when_recent(self, service):
        alert = _make_alert(level="WARN", triggered_hours_ago=1)
        assert service._should_escalate(alert) is False

    def test_no_triggered_at_returns_false(self, service):
        alert = _make_alert()
        alert.triggered_at = None
        assert service._should_escalate(alert) is False


class TestEscalateAlert:
    def test_escalates_level(self, service):
        alert = _make_alert(level="WARN")
        with patch.object(service, "_send_escalation_notification"):
            service._escalate_alert(alert)
        assert alert.alert_level == "HIGH"

    def test_adds_history_to_alert_data(self, service):
        alert = _make_alert(level="INFO")
        alert.alert_data = None
        with patch.object(service, "_send_escalation_notification"):
            service._escalate_alert(alert)
        data = json.loads(alert.alert_data)
        assert "escalation_history" in data
        assert len(data["escalation_history"]) == 1
        assert data["escalation_history"][0]["from_level"] == "INFO"
        assert data["escalation_history"][0]["to_level"] == "WARN"

    def test_no_escalation_for_unknown_level(self, service):
        alert = _make_alert(level="UNKNOWN")
        original_level = alert.alert_level
        with patch.object(service, "_send_escalation_notification"):
            service._escalate_alert(alert)
        # no valid escalation path, should remain unchanged
        assert alert.alert_level == original_level


class TestCheckAndEscalate:
    def test_no_pending_alerts_returns_zero(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = service.check_and_escalate()
        assert result["checked"] == 0
        assert result["escalated"] == 0
        assert result["errors"] == []

    def test_escalates_overdue_alerts(self, service, mock_db):
        alert = _make_alert(level="WARN", triggered_hours_ago=48)
        mock_db.query.return_value.filter.return_value.all.return_value = [alert]
        with patch.object(service, "_send_escalation_notification"):
            result = service.check_and_escalate()
        assert result["escalated"] == 1
        mock_db.commit.assert_called_once()

    def test_recent_alerts_not_escalated(self, service, mock_db):
        alert = _make_alert(level="WARN", triggered_hours_ago=1)
        mock_db.query.return_value.filter.return_value.all.return_value = [alert]
        result = service.check_and_escalate()
        assert result["escalated"] == 0
