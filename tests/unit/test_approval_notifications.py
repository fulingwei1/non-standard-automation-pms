# -*- coding: utf-8 -*-
"""Tests for ecn_notification/approval_notifications.py"""

from unittest.mock import MagicMock, patch

import pytest


class TestApprovalNotifications:
    def setup_method(self):
        self.db = MagicMock()

    @patch("app.services.ecn_notification.approval_notifications.NotificationDispatcher")
    @patch("app.services.ecn_notification.approval_notifications.find_users_by_role")
    def test_notify_approval_assigned_no_approver(self, mock_find, mock_dispatcher):
        from app.services.ecn_notification.approval_notifications import notify_approval_assigned
        mock_find.return_value = []
        ecn = MagicMock()
        approval = MagicMock()
        # No approver_id and no role users - should handle gracefully
        notify_approval_assigned(self.db, ecn, approval, approver_id=None)

    @patch("app.services.ecn_notification.approval_notifications.NotificationDispatcher")
    def test_notify_approval_assigned_with_approver(self, mock_dispatcher):
        from app.services.ecn_notification.approval_notifications import notify_approval_assigned
        ecn = MagicMock()
        ecn.id = 1
        ecn.ecn_number = "ECN-001"
        approval = MagicMock()
        approval.due_date = None  # avoid MagicMock comparison with date
        notify_approval_assigned(self.db, ecn, approval, approver_id=5)
