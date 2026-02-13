# -*- coding: utf-8 -*-
"""Tests for approval_engine/notify/basic_notifications.py"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime


class TestBasicNotificationsMixin:
    def _make_instance(self):
        from app.services.approval_engine.notify.basic_notifications import BasicNotificationsMixin
        obj = BasicNotificationsMixin()
        obj._send_notification = MagicMock()
        obj.db = MagicMock()
        return obj

    def test_notify_pending(self):
        obj = self._make_instance()
        task = MagicMock()
        task.instance.title = "Test Approval"
        task.instance.summary = "Summary"
        task.instance.urgency = "NORMAL"
        task.instance.created_at = datetime(2025, 1, 1)
        task.assignee_id = 1
        task.instance.id = 10
        task.id = 20
        obj.notify_pending(task)
        obj._send_notification.assert_called_once()
        notification = obj._send_notification.call_args[0][0]
        assert notification['type'] == 'APPROVAL_PENDING'
        assert notification['receiver_id'] == 1

    def test_notify_approved(self):
        obj = self._make_instance()
        instance = MagicMock(title="Test", initiator_id=2, id=10, created_at=datetime(2025, 1, 1))
        obj.notify_approved(instance)
        notification = obj._send_notification.call_args[0][0]
        assert notification['type'] == 'APPROVAL_APPROVED'

    def test_notify_rejected(self):
        obj = self._make_instance()
        instance = MagicMock(title="Test", initiator_id=3, id=10, created_at=datetime(2025, 1, 1))
        obj.notify_rejected(instance, rejector_name="Admin", reject_comment="Not OK")
        notification = obj._send_notification.call_args[0][0]
        assert 'Admin' in notification['content']
        assert 'Not OK' in notification['content']

    def test_notify_cc(self):
        obj = self._make_instance()
        cc = MagicMock()
        cc.instance.title = "CC Test"
        cc.instance.summary = "CC Summary"
        cc.instance.id = 10
        cc.instance.created_at = datetime(2025, 1, 1)
        cc.cc_user_id = 5
        obj.notify_cc(cc)
        notification = obj._send_notification.call_args[0][0]
        assert notification['receiver_id'] == 5
