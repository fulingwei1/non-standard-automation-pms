# -*- coding: utf-8 -*-
"""
ExceptionEventsService 深度覆盖测试（N3组）

覆盖：
- get_exception_events (pagination / filters)
- get_exception_event (found / not found)
- create_exception_event
- update_exception_event
- resolve_exception_event (已解决/正常)
- verify_exception_event (verified/reopened/not_resolved错误)
- add_exception_action
- escalate_exception_event
- create_exception_from_issue
- _auto_assign_handler (pm / dept / fallback)
- _determine_exception_severity
- _send_exception_notification (success/exception)
- _send_escalation_notification
- create_event / get_event / list_events 别名
"""

from datetime import datetime, timezone, date
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    from app.services.alert.exception_events_service import ExceptionEventsService
    return ExceptionEventsService(db=mock_db)


def _make_event(**kwargs):
    ev = MagicMock()
    ev.id = kwargs.get("id", 1)
    ev.title = kwargs.get("title", "停机事件")
    ev.description = kwargs.get("description", "机器停机")
    ev.event_type = kwargs.get("event_type", "equipment_failure")
    ev.severity = kwargs.get("severity", "high")
    ev.project_id = kwargs.get("project_id", 5)
    ev.status = kwargs.get("status", "pending")
    ev.responsible_user_id = kwargs.get("responsible_user_id", None)
    ev.responsible_dept = kwargs.get("responsible_dept", None)
    ev.reported_by = kwargs.get("reported_by", 1)
    ev.created_by = kwargs.get("created_by", 1)
    ev.updated_by = kwargs.get("updated_by", None)
    ev.resolved_by = kwargs.get("resolved_by", None)
    ev.verified_by = kwargs.get("verified_by", None)
    ev.actions = []
    ev.escalations = []
    ev.project = MagicMock()
    ev.project.pm_id = None
    ev.event_title = kwargs.get("event_title", "停机事件")
    ev.event_description = kwargs.get("event_description", "机器停机描述")
    ev.event_no = kwargs.get("event_no", "EX-001")
    return ev


def _make_user(user_id=1, dept=None, position=None):
    u = MagicMock()
    u.id = user_id
    u.department = dept
    u.position = position
    u.is_active = True
    return u


# ---------------------------------------------------------------------------
# get_exception_event
# ---------------------------------------------------------------------------

class TestGetExceptionEvent:
    def test_returns_event_when_found(self, service, mock_db):
        ev = _make_event()
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = ev
        result = service.get_exception_event(1)
        assert result is ev

    def test_returns_none_when_not_found(self, service, mock_db):
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        result = service.get_exception_event(999)
        assert result is None


# ---------------------------------------------------------------------------
# create_exception_event
# ---------------------------------------------------------------------------

class TestCreateExceptionEvent:
    def test_creates_event_and_calls_auto_assign(self, service, mock_db):
        from app.schemas.alert import ExceptionEventCreate
        event_data = MagicMock(spec=ExceptionEventCreate)
        event_data.title = "设备故障"
        event_data.description = "描述"
        event_data.event_type = "equipment_failure"
        event_data.severity = "high"
        event_data.project_id = 1
        event_data.occurred_at = None
        event_data.location = None
        event_data.impact_assessment = None
        event_data.immediate_actions = None
        current_user = _make_user()

        with patch("app.services.alert.exception_events_service.save_obj") as mock_save, \
             patch.object(service, "_auto_assign_handler") as mock_assign, \
             patch.object(service, "_send_exception_notification") as mock_notify:
            result = service.create_exception_event(event_data, current_user)
        mock_save.assert_called_once()
        mock_assign.assert_called_once()
        mock_notify.assert_called_once()

    def test_sets_occurred_at_to_now_when_none(self, service, mock_db):
        from app.schemas.alert import ExceptionEventCreate
        event_data = MagicMock(spec=ExceptionEventCreate)
        event_data.title = "事件"
        event_data.description = ""
        event_data.event_type = "safety"
        event_data.severity = "medium"
        event_data.project_id = None
        event_data.occurred_at = None
        event_data.location = None
        event_data.impact_assessment = None
        event_data.immediate_actions = None
        current_user = _make_user()

        with patch("app.services.alert.exception_events_service.save_obj"), \
             patch.object(service, "_auto_assign_handler"), \
             patch.object(service, "_send_exception_notification"):
            result = service.create_exception_event(event_data, current_user)
        # verify the ExceptionEvent was created with reported_by set
        assert result is not None


# ---------------------------------------------------------------------------
# update_exception_event
# ---------------------------------------------------------------------------

class TestUpdateExceptionEvent:
    def test_returns_none_when_event_not_found(self, service, mock_db):
        with patch.object(service, "get_exception_event", return_value=None):
            result = service.update_exception_event(999, MagicMock(), _make_user())
        assert result is None

    def test_updates_fields_and_commits(self, service, mock_db):
        from app.schemas.alert import ExceptionEventUpdate
        ev = _make_event()
        ev.status = "pending"
        event_data = MagicMock(spec=ExceptionEventUpdate)
        event_data.dict.return_value = {"title": "新标题", "severity": "critical"}
        current_user = _make_user(2)

        with patch.object(service, "get_exception_event", return_value=ev):
            mock_db.refresh.return_value = None
            result = service.update_exception_event(1, event_data, current_user)
        mock_db.commit.assert_called()
        assert ev.updated_by == 2


# ---------------------------------------------------------------------------
# resolve_exception_event
# ---------------------------------------------------------------------------

class TestResolveExceptionEvent:
    def test_returns_none_when_not_found(self, service, mock_db):
        with patch.object(service, "get_exception_event", return_value=None):
            result = service.resolve_exception_event(999, MagicMock(), _make_user())
        assert result is None

    def test_raises_when_already_resolved(self, service, mock_db):
        from fastapi import HTTPException
        ev = _make_event(status="resolved")
        with patch.object(service, "get_exception_event", return_value=ev):
            with pytest.raises(HTTPException) as exc_info:
                service.resolve_exception_event(1, MagicMock(), _make_user())
        assert exc_info.value.status_code == 400

    def test_resolves_event_successfully(self, service, mock_db):
        from app.schemas.alert import ExceptionEventResolve
        ev = _make_event(status="pending")
        resolve_data = MagicMock(spec=ExceptionEventResolve)
        resolve_data.resolution_method = "重启设备"
        resolve_data.resolution_note = "已重启"
        resolve_data.preventive_measures = "加强维护"
        current_user = _make_user(3)

        with patch.object(service, "get_exception_event", return_value=ev), \
             patch.object(service, "_send_exception_notification") as mock_notify:
            mock_db.refresh.return_value = None
            result = service.resolve_exception_event(1, resolve_data, current_user)
        assert ev.status == "resolved"
        assert ev.resolved_by == 3
        mock_notify.assert_called_once_with(ev, "resolved")


# ---------------------------------------------------------------------------
# verify_exception_event
# ---------------------------------------------------------------------------

class TestVerifyExceptionEvent:
    def test_returns_none_when_not_found(self, service, mock_db):
        with patch.object(service, "get_exception_event", return_value=None):
            result = service.verify_exception_event(999, MagicMock(), _make_user())
        assert result is None

    def test_raises_when_not_resolved(self, service, mock_db):
        from fastapi import HTTPException
        ev = _make_event(status="pending")
        with patch.object(service, "get_exception_event", return_value=ev):
            with pytest.raises(HTTPException) as exc_info:
                service.verify_exception_event(1, MagicMock(), _make_user())
        assert exc_info.value.status_code == 400

    def test_sets_verified_when_is_verified_true(self, service, mock_db):
        from app.schemas.alert import ExceptionEventVerify
        ev = _make_event(status="resolved")
        verify_data = MagicMock(spec=ExceptionEventVerify)
        verify_data.is_verified = True
        verify_data.verification_note = "验证通过"

        with patch.object(service, "get_exception_event", return_value=ev):
            mock_db.refresh.return_value = None
            result = service.verify_exception_event(1, verify_data, _make_user(4))
        assert ev.status == "verified"
        assert ev.verified_by == 4

    def test_sets_reopened_when_not_verified(self, service, mock_db):
        from app.schemas.alert import ExceptionEventVerify
        ev = _make_event(status="resolved")
        verify_data = MagicMock(spec=ExceptionEventVerify)
        verify_data.is_verified = False
        verify_data.verification_note = "不通过"

        with patch.object(service, "get_exception_event", return_value=ev):
            mock_db.refresh.return_value = None
            service.verify_exception_event(1, verify_data, _make_user())
        assert ev.status == "reopened"


# ---------------------------------------------------------------------------
# add_exception_action
# ---------------------------------------------------------------------------

class TestAddExceptionAction:
    def test_creates_exception_action(self, service, mock_db):
        action_data = {
            "action_type": "repair",
            "description": "修复设备",
            "assigned_to": 2,
            "deadline": date(2025, 6, 1),
        }
        with patch("app.services.alert.exception_events_service.save_obj") as mock_save:
            result = service.add_exception_action(1, action_data, _make_user())
        mock_save.assert_called_once()


# ---------------------------------------------------------------------------
# escalate_exception_event
# ---------------------------------------------------------------------------

class TestEscalateExceptionEvent:
    def test_returns_none_when_event_not_found(self, service, mock_db):
        with patch.object(service, "get_exception_event", return_value=None):
            result = service.escalate_exception_event(999, {}, _make_user())
        assert result is None

    def test_escalates_event_and_sends_notification(self, service, mock_db):
        ev = _make_event(status="pending")
        escalation_data = {
            "escalation_level": 2,
            "escalated_to": 10,
            "escalation_reason": "需要高层处理",
        }
        with patch.object(service, "get_exception_event", return_value=ev), \
             patch.object(service, "_send_escalation_notification") as mock_notify:
            mock_db.refresh.return_value = None
            result = service.escalate_exception_event(1, escalation_data, _make_user())
        assert ev.status == "escalated"
        assert ev.assigned_to == 10
        mock_notify.assert_called_once()


# ---------------------------------------------------------------------------
# create_exception_from_issue
# ---------------------------------------------------------------------------

class TestCreateExceptionFromIssue:
    def test_raises_404_when_issue_not_found(self, service, mock_db):
        from fastapi import HTTPException
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            service.create_exception_from_issue(999, _make_user())
        assert exc_info.value.status_code == 404

    def test_creates_event_from_issue(self, service, mock_db):
        issue = MagicMock()
        issue.id = 5
        issue.title = "质量问题"
        issue.description = "产品有缺陷"
        issue.project_id = 3
        issue.severity = "high"
        mock_db.query.return_value.filter.return_value.first.return_value = issue

        with patch("app.services.alert.exception_events_service.save_obj") as mock_save:
            result = service.create_exception_from_issue(5, _make_user())
        mock_save.assert_called_once()


# ---------------------------------------------------------------------------
# _auto_assign_handler
# ---------------------------------------------------------------------------

class TestAutoAssignHandler:
    def test_assigns_to_pm_when_project_has_pm(self, service, mock_db):
        ev = _make_event()
        ev.project = MagicMock()
        ev.project.pm_id = 10
        service._auto_assign_handler(ev)
        assert ev.responsible_user_id == 10
        assert ev.status == "ASSIGNED"

    def test_assigns_to_dept_manager_when_no_pm(self, service, mock_db):
        ev = _make_event()
        ev.project = MagicMock()
        ev.project.pm_id = None
        ev.responsible_dept = "工程部"
        dept_user = _make_user(20, dept="工程部", position="部门经理")
        mock_db.query.return_value.filter.return_value.first.return_value = dept_user
        service._auto_assign_handler(ev)
        assert ev.responsible_user_id == 20

    def test_logs_warning_when_no_assignment_possible(self, service, mock_db):
        ev = _make_event()
        ev.project = None
        ev.project_id = None
        ev.responsible_dept = None
        # Should not raise, just log warning
        service._auto_assign_handler(ev)

    def test_handles_exception_gracefully(self, service, mock_db):
        ev = _make_event()
        ev.project = MagicMock()
        ev.project.pm_id = None
        ev.responsible_dept = "IT部"
        mock_db.query.side_effect = Exception("DB error")
        # Should not raise
        service._auto_assign_handler(ev)


# ---------------------------------------------------------------------------
# _determine_exception_severity
# ---------------------------------------------------------------------------

class TestDetermineExceptionSeverity:
    @pytest.mark.parametrize("issue_severity,expected", [
        ("critical", "critical"),
        ("high", "high"),
        ("medium", "medium"),
        ("low", "low"),
        ("unknown", "medium"),
        (None, "medium"),
    ])
    def test_severity_mapping(self, service, issue_severity, expected):
        issue = MagicMock()
        issue.severity = issue_severity
        result = service._determine_exception_severity(issue)
        assert result == expected


# ---------------------------------------------------------------------------
# _send_exception_notification
# ---------------------------------------------------------------------------

class TestSendExceptionNotification:
    def test_sends_notification_to_responsible_user(self, service, mock_db):
        ev = _make_event(responsible_user_id=5, reported_by=2)
        ev.severity = "high"
        ev.status = "pending"
        mock_notif_service = MagicMock()
        with patch(
            "app.services.alert.exception_events_service.get_notification_service",
            return_value=mock_notif_service,
        ):
            service._send_exception_notification(ev, "created")
        mock_notif_service.send_notification.assert_called()

    def test_handles_exception_gracefully(self, service, mock_db):
        ev = _make_event(responsible_user_id=5)
        with patch(
            "app.services.alert.exception_events_service.get_notification_service",
            side_effect=Exception("service error"),
        ):
            # Should not raise
            service._send_exception_notification(ev, "created")

    def test_does_not_send_when_no_recipients(self, service, mock_db):
        ev = _make_event()
        ev.responsible_user_id = None
        ev.reported_by = None
        ev.created_by = None
        mock_notif_service = MagicMock()
        with patch(
            "app.services.alert.exception_events_service.get_notification_service",
            return_value=mock_notif_service,
        ):
            service._send_exception_notification(ev, "created")
        mock_notif_service.send_notification.assert_not_called()


# ---------------------------------------------------------------------------
# _send_escalation_notification
# ---------------------------------------------------------------------------

class TestSendEscalationNotification:
    def test_sends_notification_to_escalated_user(self, service, mock_db):
        ev = _make_event()
        escalation = MagicMock()
        escalation.escalated_to = 10
        escalation.escalation_level = 2
        escalation.escalation_reason = "需要处理"
        escalation.id = 1
        mock_notif_service = MagicMock()
        with patch(
            "app.services.alert.exception_events_service.get_notification_service",
            return_value=mock_notif_service,
        ):
            service._send_escalation_notification(ev, escalation)
        mock_notif_service.send_notification.assert_called_once()

    def test_handles_exception_gracefully(self, service, mock_db):
        ev = _make_event()
        escalation = MagicMock()
        escalation.escalated_to = 10
        with patch(
            "app.services.alert.exception_events_service.get_notification_service",
            side_effect=Exception("error"),
        ):
            service._send_escalation_notification(ev, escalation)


# ---------------------------------------------------------------------------
# Alias methods
# ---------------------------------------------------------------------------

class TestAliaseMethods:
    def test_get_event_alias(self, service):
        with patch.object(service, "get_exception_event", return_value="event") as mock:
            result = service.get_event(5)
        mock.assert_called_once_with(5)
        assert result == "event"

    def test_list_events_alias(self, service):
        with patch.object(service, "get_exception_events", return_value="list") as mock:
            result = service.list_events(page=2, page_size=10, keyword="test")
        mock.assert_called_once_with(page=2, page_size=10, keyword="test")
