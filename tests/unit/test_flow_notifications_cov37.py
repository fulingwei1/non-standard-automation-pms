# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - 审批流程变更通知
tests/unit/test_flow_notifications_cov37.py
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock

pytest.importorskip("app.services.approval_engine.notify.flow_notifications")

from app.services.approval_engine.notify.flow_notifications import FlowNotificationsMixin


class ConcreteFlow(FlowNotificationsMixin):
    def __init__(self):
        self._sent = []

    def _send_notification(self, notification):
        self._sent.append(notification)


def _make_instance(title="测试审批"):
    inst = MagicMock()
    inst.id = 1
    inst.title = title
    return inst


def _make_task(assignee_id=20, instance=None):
    task = MagicMock()
    task.id = 2
    task.assignee_id = assignee_id
    task.instance = instance or _make_instance()
    return task


class TestFlowNotifications:
    def setup_method(self):
        self.notifier = ConcreteFlow()

    def test_notify_withdrawn_sends_to_all_users(self):
        instance = _make_instance()
        self.notifier.notify_withdrawn(instance, affected_user_ids=[1, 2, 3])
        assert len(self.notifier._sent) == 3

    def test_notify_withdrawn_type(self):
        instance = _make_instance()
        self.notifier.notify_withdrawn(instance, affected_user_ids=[5])
        assert self.notifier._sent[0]["type"] == "APPROVAL_WITHDRAWN"

    def test_notify_withdrawn_empty_user_list(self):
        instance = _make_instance()
        self.notifier.notify_withdrawn(instance, affected_user_ids=[])
        assert len(self.notifier._sent) == 0

    def test_notify_transferred_sends_to_assignee(self):
        task = _make_task(assignee_id=33)
        self.notifier.notify_transferred(task, from_user_id=10, from_user_name="张三")
        assert len(self.notifier._sent) == 1
        assert self.notifier._sent[0]["receiver_id"] == 33

    def test_notify_transferred_type(self):
        task = _make_task()
        self.notifier.notify_transferred(task, from_user_id=10)
        assert self.notifier._sent[0]["type"] == "APPROVAL_TRANSFERRED"

    def test_notify_transferred_without_name(self):
        task = _make_task()
        self.notifier.notify_transferred(task, from_user_id=10, from_user_name=None)
        assert len(self.notifier._sent) == 1

    def test_notify_withdrawn_title_contains_instance_title(self):
        instance = _make_instance(title="变更申请")
        self.notifier.notify_withdrawn(instance, affected_user_ids=[1])
        assert "变更申请" in self.notifier._sent[0]["title"]
