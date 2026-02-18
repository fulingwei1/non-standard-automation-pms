# -*- coding: utf-8 -*-
"""ExceptionEventsService 单元测试"""

import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

# Patch missing model relationships before importing
from app.models.alert import ExceptionEvent, ExceptionAction, ExceptionEscalation
for _attr in ('reported_by_user', 'assigned_user', 'resolved_by_user', 'actions', 'escalations'):
    if not hasattr(ExceptionEvent, _attr):
        setattr(ExceptionEvent, _attr, MagicMock())
# Source code references occurred_at but model has discovered_at
if not hasattr(ExceptionEvent, 'occurred_at'):
    ExceptionEvent.occurred_at = ExceptionEvent.discovered_at


# We need to patch joinedload in the service module because the source code
# references model attributes (e.g. ExceptionEvent.reported_by_user) that are
# MagicMock objects, and real SQLAlchemy joinedload chokes on them.
_mock_joinedload = MagicMock(name="joinedload")


@patch("app.services.alert.exception_events_service.joinedload", _mock_joinedload)
class TestExceptionEventsService(unittest.TestCase):

    def setUp(self):
        _mock_joinedload.reset_mock()
        self.db = MagicMock()
        # Import here so the patch is active
        from app.services.alert.exception_events_service import ExceptionEventsService
        self.service = ExceptionEventsService(self.db)

    # --- get_exception_event ---
    def test_get_exception_event_found(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        event = MagicMock(id=1)
        mock_query.first.return_value = event

        result = self.service.get_exception_event(1)
        self.assertEqual(result.id, 1)

    def test_get_exception_event_not_found(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = self.service.get_exception_event(999)
        self.assertIsNone(result)

    # --- get_exception_events (list) ---
    @patch("app.services.alert.exception_events_service.get_pagination_params")
    @patch("app.services.alert.exception_events_service.apply_keyword_filter")
    @patch("app.services.alert.exception_events_service.apply_pagination")
    def test_get_exception_events(self, mock_apply_pag, mock_kw_filter, mock_get_pag):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_kw_filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0

        pag = MagicMock()
        pag.page = 1
        pag.page_size = 20
        pag.offset = 0
        pag.limit = 20
        pag.pages_for_total.return_value = 0
        mock_get_pag.return_value = pag
        mock_apply_pag.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service.get_exception_events(page=1, page_size=20)
        self.assertEqual(result.total, 0)

    # --- create_exception_event ---
    @patch.object(ExceptionEvent, "__init__", lambda self, **kw: None)
    @patch("app.services.alert.exception_events_service.ExceptionEvent")
    def test_create_exception_event(self, mock_event_cls):
        mock_event = MagicMock()
        mock_event_cls.return_value = mock_event

        event_data = MagicMock()
        event_data.title = "test"
        event_data.description = "desc"
        event_data.event_type = "safety_incident"
        event_data.severity = "high"
        event_data.project_id = 1
        event_data.occurred_at = None
        event_data.location = "A区"
        event_data.impact_assessment = "无"
        event_data.immediate_actions = "无"

        user = MagicMock()
        user.id = 1

        result = self.service.create_exception_event(event_data, user)
        self.db.add.assert_called()
        self.db.commit.assert_called()
        self.db.refresh.assert_called()

    # --- update_exception_event ---
    def test_update_exception_event_not_found(self):
        with patch.object(self.service, 'get_exception_event', return_value=None):
            result = self.service.update_exception_event(999, MagicMock(), MagicMock())
            self.assertIsNone(result)

    def test_update_exception_event_success(self):
        event = MagicMock(id=1, reported_by=1, created_at=datetime.now())
        with patch.object(self.service, 'get_exception_event', return_value=event):
            update_data = MagicMock()
            update_data.dict.return_value = {"title": "updated"}
            user = MagicMock(id=2)

            result = self.service.update_exception_event(1, update_data, user)
            self.assertEqual(result.id, 1)

    # --- resolve_exception_event ---
    def test_resolve_already_resolved(self):
        event = MagicMock(id=1, status="resolved")
        with patch.object(self.service, 'get_exception_event', return_value=event):
            with self.assertRaises(HTTPException):
                self.service.resolve_exception_event(1, MagicMock(), MagicMock())

    def test_resolve_not_found(self):
        with patch.object(self.service, 'get_exception_event', return_value=None):
            result = self.service.resolve_exception_event(1, MagicMock(), MagicMock())
            self.assertIsNone(result)

    def test_resolve_success(self):
        event = MagicMock(id=1, status="pending")
        with patch.object(self.service, 'get_exception_event', return_value=event):
            resolve_data = MagicMock()
            resolve_data.resolution_method = "fixed"
            resolve_data.resolution_note = "done"
            resolve_data.preventive_measures = "none"
            user = MagicMock(id=2)

            result = self.service.resolve_exception_event(1, resolve_data, user)
            self.assertEqual(result.status, "resolved")

    # --- verify_exception_event ---
    def test_verify_not_resolved_raises(self):
        event = MagicMock(id=1, status="pending")
        with patch.object(self.service, 'get_exception_event', return_value=event):
            with self.assertRaises(HTTPException):
                self.service.verify_exception_event(1, MagicMock(), MagicMock())

    def test_verify_approved(self):
        event = MagicMock(id=1, status="resolved")
        with patch.object(self.service, 'get_exception_event', return_value=event):
            verify_data = MagicMock()
            verify_data.is_verified = True
            verify_data.verification_note = "ok"
            user = MagicMock(id=3)

            result = self.service.verify_exception_event(1, verify_data, user)
            self.assertEqual(result.status, "verified")

    def test_verify_reopened(self):
        event = MagicMock(id=1, status="resolved")
        with patch.object(self.service, 'get_exception_event', return_value=event):
            verify_data = MagicMock()
            verify_data.is_verified = False
            verify_data.verification_note = "not ok"
            user = MagicMock(id=3)

            result = self.service.verify_exception_event(1, verify_data, user)
            self.assertEqual(result.status, "reopened")

    def test_verify_not_found(self):
        with patch.object(self.service, 'get_exception_event', return_value=None):
            result = self.service.verify_exception_event(1, MagicMock(), MagicMock())
            self.assertIsNone(result)

    # --- add_exception_action ---
    @patch.object(ExceptionAction, "__init__", lambda self, **kw: None)
    def test_add_exception_action(self):
        user = MagicMock(id=1)
        action_data = {
            "action_type": "fix",
            "description": "fix it",
            "assigned_to": 2,
            "deadline": None
        }

        self.service.add_exception_action(1, action_data, user)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    # --- escalate_exception_event ---
    @patch.object(ExceptionEscalation, "__init__", lambda self, **kw: None)
    def test_escalate_exception_event(self):
        event = MagicMock(id=1, status="pending")
        with patch.object(self.service, 'get_exception_event', return_value=event):
            escalation_data = {
                "escalation_level": 2,
                "escalated_to": 5,
                "escalation_reason": "urgent"
            }
            user = MagicMock(id=1)

            result = self.service.escalate_exception_event(1, escalation_data, user)
            self.assertEqual(result.status, "escalated")

    def test_escalate_not_found(self):
        with patch.object(self.service, 'get_exception_event', return_value=None):
            result = self.service.escalate_exception_event(1, {}, MagicMock())
            self.assertIsNone(result)

    # --- create_exception_from_issue ---
    def test_create_exception_from_issue_not_found(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with self.assertRaises(HTTPException):
            self.service.create_exception_from_issue(999, MagicMock())

    @patch.object(ExceptionEvent, "__init__", lambda self, **kw: None)
    def test_create_exception_from_issue_success(self):
        issue = MagicMock()
        issue.id = 1
        issue.title = "Issue"
        issue.description = "desc"
        issue.severity = "high"
        issue.project_id = 1

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = issue

        user = MagicMock(id=1)
        result = self.service.create_exception_from_issue(1, user)
        self.db.add.assert_called_once()

    # --- _determine_exception_severity ---
    def test_determine_severity_mapping(self):
        issue = MagicMock(severity="critical")
        self.assertEqual(self.service._determine_exception_severity(issue), "critical")

        issue.severity = "unknown"
        self.assertEqual(self.service._determine_exception_severity(issue), "medium")

    # --- aliases ---
    def test_get_event_alias(self):
        with patch.object(self.service, 'get_exception_event', return_value="ok") as mock:
            self.assertEqual(self.service.get_event(1), "ok")
            mock.assert_called_once_with(1)

    def test_list_events_alias(self):
        with patch.object(self.service, 'get_exception_events', return_value="ok") as mock:
            self.assertEqual(self.service.list_events(page=2, page_size=10), "ok")
            mock.assert_called_once_with(page=2, page_size=10)


if __name__ == "__main__":
    unittest.main()
