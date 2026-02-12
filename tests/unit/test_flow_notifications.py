# -*- coding: utf-8 -*-
"""审批流程变更通知 单元测试"""
from unittest.mock import MagicMock

import pytest

from app.services.approval_engine.notify.flow_notifications import FlowNotificationsMixin


def _make_mixin():
    m = FlowNotificationsMixin()
    m._send_notification = MagicMock()
    return m


def _make_instance(title="测试审批", urgency="NORMAL"):
    inst = MagicMock()
    inst.id = 1
    inst.title = title
    inst.urgency = urgency
    return inst


def _make_task(assignee_id=10, instance=None):
    t = MagicMock()
    t.id = 1
    t.assignee_id = assignee_id
    t.instance = instance or _make_instance()
    return t


class TestNotifyWithdrawn:
    def test_sends_to_all_users(self):
        m = _make_mixin()
        inst = _make_instance()
        m.notify_withdrawn(inst, [1, 2, 3])
        assert m._send_notification.call_count == 3

    def test_notification_type(self):
        m = _make_mixin()
        inst = _make_instance()
        m.notify_withdrawn(inst, [1])
        call_args = m._send_notification.call_args[0][0]
        assert call_args["type"] == "APPROVAL_WITHDRAWN"


class TestNotifyTransferred:
    def test_sends_notification(self):
        m = _make_mixin()
        task = _make_task()
        m.notify_transferred(task, from_user_id=5, from_user_name="张三")
        m._send_notification.assert_called_once()
        call_args = m._send_notification.call_args[0][0]
        assert call_args["type"] == "APPROVAL_TRANSFERRED"
        assert "张三" in call_args["content"]


class TestNotifyDelegated:
    def test_sends_notification(self):
        m = _make_mixin()
        task = _make_task()
        m.notify_delegated(task, original_user_name="李四")
        call_args = m._send_notification.call_args[0][0]
        assert call_args["type"] == "APPROVAL_DELEGATED"
        assert "李四" in call_args["content"]


class TestNotifyAddApprover:
    def test_before_position(self):
        m = _make_mixin()
        task = _make_task()
        m.notify_add_approver(task, added_by_name="王五", position="BEFORE")
        call_args = m._send_notification.call_args[0][0]
        assert "前加签" in call_args["content"]

    def test_after_position(self):
        m = _make_mixin()
        task = _make_task()
        m.notify_add_approver(task, position="AFTER")
        call_args = m._send_notification.call_args[0][0]
        assert "后加签" in call_args["content"]
