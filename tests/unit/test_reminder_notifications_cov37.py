# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - 审批提醒通知
tests/unit/test_reminder_notifications_cov37.py
"""
import pytest
from unittest.mock import MagicMock

pytest.importorskip("app.services.approval_engine.notify.reminder_notifications")

from app.services.approval_engine.notify.reminder_notifications import ReminderNotificationsMixin


class ConcreteReminder(ReminderNotificationsMixin):
    def __init__(self):
        self._sent = []

    def _send_notification(self, notification):
        self._sent.append(notification)


def _make_task(task_id=1, assignee_id=20, instance_title="测试审批", instance_id=100):
    task = MagicMock()
    task.id = task_id
    task.assignee_id = assignee_id
    instance = MagicMock()
    instance.id = instance_id
    instance.title = instance_title
    task.instance = instance
    return task


class TestReminderNotifications:
    def setup_method(self):
        self.notifier = ConcreteReminder()

    def test_notify_timeout_warning_sends_notification(self):
        task = _make_task()
        self.notifier.notify_timeout_warning(task, hours_remaining=2)
        assert len(self.notifier._sent) == 1

    def test_notify_timeout_warning_type(self):
        task = _make_task()
        self.notifier.notify_timeout_warning(task, hours_remaining=4)
        assert self.notifier._sent[0]["type"] == "APPROVAL_TIMEOUT_WARNING"

    def test_notify_timeout_warning_content_contains_hours(self):
        task = _make_task()
        self.notifier.notify_timeout_warning(task, hours_remaining=3)
        assert "3" in self.notifier._sent[0]["content"]

    def test_notify_timeout_warning_receiver_is_assignee(self):
        task = _make_task(assignee_id=55)
        self.notifier.notify_timeout_warning(task, hours_remaining=1)
        assert self.notifier._sent[0]["receiver_id"] == 55

    def test_notify_remind_sends_notification(self):
        task = _make_task()
        self.notifier.notify_remind(task, reminder_id=9, reminder_name="赵六")
        assert len(self.notifier._sent) == 1

    def test_notify_remind_type(self):
        task = _make_task()
        self.notifier.notify_remind(task, reminder_id=9)
        assert self.notifier._sent[0]["type"] == "APPROVAL_REMIND"

    def test_notify_remind_without_name(self):
        task = _make_task()
        self.notifier.notify_remind(task, reminder_id=9, reminder_name=None)
        content = self.notifier._sent[0]["content"]
        # No "催促" in content when name is None
        assert "催促" not in content

    def test_notify_remind_with_name_includes_reminder(self):
        task = _make_task(instance_title="紧急审批")
        self.notifier.notify_remind(task, reminder_id=9, reminder_name="张经理")
        assert "张经理" in self.notifier._sent[0]["content"]
