# -*- coding: utf-8 -*-
"""
approval_engine/engine/notify.py 单元测试
对齐当前 notify mixin 契约。
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.approval_engine.notify import ApprovalNotifyService


def _make_instance():
    instance = MagicMock()
    instance.id = 1
    instance.title = "TEST-001"
    instance.summary = "summary"
    instance.initiator_id = 99
    instance.created_at = None
    instance.urgency = "NORMAL"
    return instance


@pytest.mark.unit
class TestNotifyPending:
    def test_notify_pending_success(self):
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)
        service._send_notification = MagicMock()

        mock_task = MagicMock()
        mock_task.id = 100
        mock_task.assignee_id = 50
        mock_task.instance = _make_instance()

        service.notify_pending(mock_task)
        service._send_notification.assert_called_once()


@pytest.mark.unit
class TestNotifyApproved:
    def test_notify_approved_success(self):
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)
        service._send_notification = MagicMock()

        service.notify_approved(_make_instance())
        service._send_notification.assert_called_once()

    def test_notify_approved_with_extra_context(self):
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)
        service._send_notification = MagicMock()

        service.notify_approved(_make_instance(), extra_context={"custom_field": "value"})
        service._send_notification.assert_called_once()


@pytest.mark.unit
class TestNotifyRejected:
    def test_notify_rejected_success(self):
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)
        service._send_notification = MagicMock()

        service.notify_rejected(_make_instance(), rejector_name="张经理", reject_comment="不同意")
        service._send_notification.assert_called_once()


@pytest.mark.unit
class TestNotifyCc:
    def test_notify_cc_success(self):
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)
        service._send_notification = MagicMock()

        cc_record = MagicMock()
        cc_record.cc_user_id = 100
        cc_record.instance = _make_instance()

        service.notify_cc(cc_record)
        service._send_notification.assert_called_once()


@pytest.mark.unit
class TestNotifyTimeoutWarning:
    def test_notify_timeout_warning_success(self):
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)
        service._send_notification = MagicMock()

        task = MagicMock()
        task.id = 100
        task.assignee_id = 50
        task.instance = _make_instance()

        service.notify_timeout_warning(task, hours_remaining=24)
        service._send_notification.assert_called_once()


@pytest.mark.unit
class TestGenerateDedupKey:
    def test_generate_dedup_key(self):
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)

        notification = {
            "instance_id": 1,
            "node_id": 10,
            "task_id": 100,
            "type": "APPROVED",
            "receiver_id": 50,
        }

        key = service._generate_dedup_key(notification)
        assert isinstance(key, str)
        assert len(key) == 32

    def test_is_duplicate_true(self):
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)

        with patch.object(service, "_check_user_preferences", return_value={"dedup_window_hours": 1}):
            service._is_duplicate("1:10:100:APPROVED:50")
            assert service._is_duplicate("1:10:100:APPROVED:50") is True

    def test_is_duplicate_false(self):
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)

        with patch.object(service, "_check_user_preferences", return_value={"dedup_window_hours": 0}):
            assert service._is_duplicate("1:10:100:APPROVED:50") is False


@pytest.mark.unit
class TestNotifyServiceIntegration:
    def test_all_methods_callable(self):
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)

        methods = [
            "notify_pending",
            "notify_approved",
            "notify_rejected",
            "notify_cc",
            "notify_timeout_warning",
        ]

        for method in methods:
            assert hasattr(service, method)
