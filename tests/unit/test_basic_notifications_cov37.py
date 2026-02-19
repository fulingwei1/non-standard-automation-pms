# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - 审批基础通知
tests/unit/test_basic_notifications_cov37.py
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, call

pytest.importorskip("app.services.approval_engine.notify.basic_notifications")

from app.services.approval_engine.notify.basic_notifications import BasicNotificationsMixin


class ConcreteNotifier(BasicNotificationsMixin):
    def __init__(self):
        self._sent = []

    def _send_notification(self, notification):
        self._sent.append(notification)


def _make_task(task_id=1, assignee_id=10, instance_title="测试审批"):
    task = MagicMock()
    task.id = task_id
    task.assignee_id = assignee_id
    instance = MagicMock()
    instance.id = 100
    instance.title = instance_title
    instance.summary = "这是摘要"
    instance.urgency = "NORMAL"
    instance.initiator_id = 5
    instance.created_at = datetime(2025, 6, 1, 12, 0, 0)
    task.instance = instance
    return task


def _make_instance(instance_id=100, title="测试审批", initiator_id=5):
    instance = MagicMock()
    instance.id = instance_id
    instance.title = title
    instance.initiator_id = initiator_id
    instance.created_at = datetime(2025, 6, 1, 12, 0, 0)
    return instance


class TestBasicNotifications:
    def setup_method(self):
        self.notifier = ConcreteNotifier()

    def test_notify_pending_sends_notification(self):
        task = _make_task()
        self.notifier.notify_pending(task)
        assert len(self.notifier._sent) == 1
        n = self.notifier._sent[0]
        assert n["type"] == "APPROVAL_PENDING"
        assert n["receiver_id"] == 10

    def test_notify_pending_title_contains_instance_title(self):
        task = _make_task(instance_title="采购审批")
        self.notifier.notify_pending(task)
        assert "采购审批" in self.notifier._sent[0]["title"]

    def test_notify_approved_sends_to_initiator(self):
        instance = _make_instance(initiator_id=7)
        self.notifier.notify_approved(instance)
        assert len(self.notifier._sent) == 1
        n = self.notifier._sent[0]
        assert n["type"] == "APPROVAL_APPROVED"
        assert n["receiver_id"] == 7

    def test_notify_approved_title_contains_instance_title(self):
        instance = _make_instance(title="合同审批")
        self.notifier.notify_approved(instance)
        assert "合同审批" in self.notifier._sent[0]["title"]

    def test_notify_pending_includes_task_id(self):
        task = _make_task(task_id=42)
        self.notifier.notify_pending(task)
        assert self.notifier._sent[0]["task_id"] == 42

    def test_notify_pending_with_extra_context(self):
        task = _make_task()
        self.notifier.notify_pending(task, extra_context={"foo": "bar"})
        assert len(self.notifier._sent) == 1
