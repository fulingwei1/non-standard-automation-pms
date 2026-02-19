# -*- coding: utf-8 -*-
"""
Unit tests for ReminderNotificationsMixin (第三十一批)
"""
from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest

from app.services.approval_engine.notify.reminder_notifications import (
    ReminderNotificationsMixin,
)


class ConcreteReminder(ReminderNotificationsMixin):
    """Concrete subclass that records sent notifications."""

    def __init__(self):
        self._sent = []

    def _send_notification(self, notification):
        self._sent.append(notification)


@pytest.fixture
def reminder():
    return ConcreteReminder()


@pytest.fixture
def mock_task():
    task = MagicMock()
    task.id = 42
    task.assignee_id = 7
    task.instance.id = 100
    task.instance.title = "采购申请审批"
    return task


# ---------------------------------------------------------------------------
# notify_timeout_warning
# ---------------------------------------------------------------------------

class TestNotifyTimeoutWarning:
    def test_sends_notification_with_correct_type(self, reminder, mock_task):
        reminder.notify_timeout_warning(mock_task, hours_remaining=3)
        assert len(reminder._sent) == 1
        notification = reminder._sent[0]
        assert notification["type"] == "APPROVAL_TIMEOUT_WARNING"

    def test_notification_contains_hours_remaining(self, reminder, mock_task):
        reminder.notify_timeout_warning(mock_task, hours_remaining=5)
        notification = reminder._sent[0]
        assert "5" in notification["content"]

    def test_receiver_id_set_correctly(self, reminder, mock_task):
        reminder.notify_timeout_warning(mock_task, hours_remaining=2)
        notification = reminder._sent[0]
        assert notification["receiver_id"] == mock_task.assignee_id

    def test_urgency_is_urgent(self, reminder, mock_task):
        reminder.notify_timeout_warning(mock_task, hours_remaining=1)
        notification = reminder._sent[0]
        assert notification["urgency"] == "URGENT"

    def test_title_includes_instance_title(self, reminder, mock_task):
        reminder.notify_timeout_warning(mock_task, hours_remaining=2)
        notification = reminder._sent[0]
        assert mock_task.instance.title in notification["title"]

    def test_extra_context_accepted(self, reminder, mock_task):
        """extra_context 参数不应导致异常"""
        reminder.notify_timeout_warning(
            mock_task, hours_remaining=4, extra_context={"foo": "bar"}
        )
        assert len(reminder._sent) == 1


# ---------------------------------------------------------------------------
# notify_remind
# ---------------------------------------------------------------------------

class TestNotifyRemind:
    def test_sends_remind_notification(self, reminder, mock_task):
        reminder.notify_remind(mock_task, reminder_id=3)
        assert len(reminder._sent) == 1
        notification = reminder._sent[0]
        assert notification["type"] == "APPROVAL_REMIND"

    def test_reminder_name_included_in_content(self, reminder, mock_task):
        reminder.notify_remind(mock_task, reminder_id=3, reminder_name="张三")
        notification = reminder._sent[0]
        assert "张三" in notification["content"]

    def test_no_reminder_name_ok(self, reminder, mock_task):
        reminder.notify_remind(mock_task, reminder_id=3, reminder_name=None)
        notification = reminder._sent[0]
        assert notification["type"] == "APPROVAL_REMIND"
        assert "None" not in notification["content"]

    def test_instance_id_and_task_id_in_notification(self, reminder, mock_task):
        reminder.notify_remind(mock_task, reminder_id=5)
        notification = reminder._sent[0]
        assert notification["instance_id"] == mock_task.instance.id
        assert notification["task_id"] == mock_task.id
