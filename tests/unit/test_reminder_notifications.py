# -*- coding: utf-8 -*-
"""审批提醒通知单元测试"""
import pytest
from unittest.mock import MagicMock
from app.services.approval_engine.notify.reminder_notifications import ReminderNotificationsMixin


class TestReminderNotificationsMixin:
    def setup_method(self):
        self.mixin = ReminderNotificationsMixin()
        self.mixin._send_notification = MagicMock()

    def _make_task(self):
        task = MagicMock()
        task.assignee_id = 10
        task.id = 1
        task.instance.id = 100
        task.instance.title = "测试审批"
        return task

    def test_notify_timeout_warning(self):
        task = self._make_task()
        self.mixin.notify_timeout_warning(task, 2)
        self.mixin._send_notification.assert_called_once()
        notification = self.mixin._send_notification.call_args[0][0]
        assert notification["type"] == "APPROVAL_TIMEOUT_WARNING"
        assert notification["urgency"] == "URGENT"
        assert "2" in notification["content"]

    def test_notify_remind_with_name(self):
        task = self._make_task()
        self.mixin.notify_remind(task, 5, "张三")
        notification = self.mixin._send_notification.call_args[0][0]
        assert notification["type"] == "APPROVAL_REMIND"
        assert "张三" in notification["content"]

    def test_notify_remind_without_name(self):
        task = self._make_task()
        self.mixin.notify_remind(task, 5)
        notification = self.mixin._send_notification.call_args[0][0]
        assert "张三" not in notification["content"]
