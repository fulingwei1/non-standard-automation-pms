# -*- coding: utf-8 -*-
"""Tests for ecn_notification/ecn_notifications.py"""
import pytest
from unittest.mock import MagicMock, patch


class TestNotifyEcnSubmitted:
    @patch('app.services.ecn_notification.ecn_notifications.NotificationDispatcher')
    def test_notify_applicant(self, mock_dispatcher_cls):
        from app.services.ecn_notification.ecn_notifications import notify_ecn_submitted
        db = MagicMock()
        ecn = MagicMock(id=1, applicant_id=10, ecn_no='ECN001', ecn_title='Test', project_id=None)
        mock_dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = mock_dispatcher
        notify_ecn_submitted(db, ecn)
        mock_dispatcher.send_notification_request.assert_called_once()

    @patch('app.services.ecn_notification.ecn_notifications.NotificationDispatcher')
    def test_notify_with_project_members(self, mock_dispatcher_cls):
        from app.services.ecn_notification.ecn_notifications import notify_ecn_submitted
        db = MagicMock()
        ecn = MagicMock(id=1, applicant_id=10, ecn_no='ECN001', ecn_title='Test',
                        ecn_type='DESIGN', change_reason='Bug', project_id=5)
        member = MagicMock(user_id=20)
        db.query.return_value.filter.return_value.all.return_value = [member]
        mock_dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = mock_dispatcher
        notify_ecn_submitted(db, ecn)
        assert mock_dispatcher.send_notification_request.call_count == 2

    @patch('app.services.ecn_notification.ecn_notifications.NotificationDispatcher')
    def test_no_applicant(self, mock_dispatcher_cls):
        from app.services.ecn_notification.ecn_notifications import notify_ecn_submitted
        db = MagicMock()
        ecn = MagicMock(id=1, applicant_id=None, project_id=None)
        mock_dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = mock_dispatcher
        notify_ecn_submitted(db, ecn)
        mock_dispatcher.send_notification_request.assert_not_called()


class TestNotifyOverdueAlert:
    @patch('app.services.ecn_notification.ecn_notifications.NotificationDispatcher')
    def test_notify_users(self, mock_dispatcher_cls):
        from app.services.ecn_notification.ecn_notifications import notify_overdue_alert
        db = MagicMock()
        mock_dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = mock_dispatcher
        alert = {'ecn_no': 'ECN001', 'message': 'Overdue', 'overdue_days': 10, 'ecn_id': 1, 'type': 'OVERDUE'}
        notify_overdue_alert(db, alert, [1, 2])
        assert mock_dispatcher.send_notification_request.call_count == 2
