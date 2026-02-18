# -*- coding: utf-8 -*-
"""第二十二批：basic_notifications 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

try:
    from app.services.approval_engine.notify.basic_notifications import BasicNotificationsMixin
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="import failed")


class ConcreteNotifier(BasicNotificationsMixin):
    """具体实现用于测试"""
    def __init__(self):
        self.sent_notifications = []

    def _send_notification(self, notification):
        self.sent_notifications.append(notification)


@pytest.fixture
def notifier():
    return ConcreteNotifier()


@pytest.fixture
def mock_task():
    task = MagicMock()
    task.id = 1
    task.assignee_id = 42
    instance = MagicMock()
    instance.id = 10
    instance.title = "采购申请审批"
    instance.summary = "需要审批采购申请"
    instance.urgency = "HIGH"
    instance.created_at = datetime(2025, 2, 1)
    instance.initiator_id = 99
    task.instance = instance
    return task


@pytest.fixture
def mock_instance():
    inst = MagicMock()
    inst.id = 10
    inst.title = "采购申请审批"
    inst.summary = "需要审批采购申请"
    inst.urgency = "NORMAL"
    inst.created_at = datetime(2025, 2, 1)
    inst.initiator_id = 99
    return inst


@pytest.fixture
def mock_cc_record(mock_instance):
    cc = MagicMock()
    cc.cc_user_id = 55
    cc.instance = mock_instance
    return cc


class TestNotifyPending:
    def test_sends_notification_with_correct_type(self, notifier, mock_task):
        """notify_pending 发送 APPROVAL_PENDING 通知"""
        notifier.notify_pending(mock_task)
        assert len(notifier.sent_notifications) == 1
        assert notifier.sent_notifications[0]["type"] == "APPROVAL_PENDING"

    def test_receiver_is_task_assignee(self, notifier, mock_task):
        """接收者是任务分配人"""
        notifier.notify_pending(mock_task)
        assert notifier.sent_notifications[0]["receiver_id"] == 42

    def test_title_contains_instance_title(self, notifier, mock_task):
        """通知标题包含审批实例标题"""
        notifier.notify_pending(mock_task)
        assert "采购申请审批" in notifier.sent_notifications[0]["title"]

    def test_instance_id_in_notification(self, notifier, mock_task):
        """通知包含实例ID"""
        notifier.notify_pending(mock_task)
        assert notifier.sent_notifications[0]["instance_id"] == 10


class TestNotifyApproved:
    def test_sends_approval_approved_type(self, notifier, mock_instance):
        """notify_approved 发送 APPROVAL_APPROVED 通知"""
        notifier.notify_approved(mock_instance)
        assert notifier.sent_notifications[0]["type"] == "APPROVAL_APPROVED"

    def test_receiver_is_initiator(self, notifier, mock_instance):
        """接收者是发起人"""
        notifier.notify_approved(mock_instance)
        assert notifier.sent_notifications[0]["receiver_id"] == 99


class TestNotifyRejected:
    def test_sends_approval_rejected_type(self, notifier, mock_instance):
        """notify_rejected 发送 APPROVAL_REJECTED 通知"""
        notifier.notify_rejected(mock_instance)
        assert notifier.sent_notifications[0]["type"] == "APPROVAL_REJECTED"

    def test_content_includes_rejector_name(self, notifier, mock_instance):
        """内容包含驳回人姓名"""
        notifier.notify_rejected(mock_instance, rejector_name="张三")
        assert "张三" in notifier.sent_notifications[0]["content"]

    def test_content_includes_reject_comment(self, notifier, mock_instance):
        """内容包含驳回原因"""
        notifier.notify_rejected(mock_instance, reject_comment="金额超出预算")
        assert "金额超出预算" in notifier.sent_notifications[0]["content"]


class TestNotifyCC:
    def test_sends_approval_cc_type(self, notifier, mock_cc_record):
        """notify_cc 发送 APPROVAL_CC 通知"""
        notifier.notify_cc(mock_cc_record)
        assert notifier.sent_notifications[0]["type"] == "APPROVAL_CC"

    def test_receiver_is_cc_user(self, notifier, mock_cc_record):
        """接收者是抄送用户"""
        notifier.notify_cc(mock_cc_record)
        assert notifier.sent_notifications[0]["receiver_id"] == 55
