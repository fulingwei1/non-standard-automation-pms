# -*- coding: utf-8 -*-
"""
approval_engine/engine/notify.py 单元测试

测试审批通知服务的各个方法
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.approval_engine.notify import ApprovalNotifyService


@pytest.mark.unit
class TestNotifyPending:
    """测试 notify_pending 方法"""

    def test_notify_pending_success(self):
        """测试通知待审批任务"""
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.business_key = "TEST-001"

        mock_node = MagicMock()
        mock_node.id = 10

        mock_task = MagicMock()
        mock_task.id = 100
        mock_task.assignee_id = 50

        service.notify_pending(mock_instance, mock_node, mock_task, extra_context=None)

        assert mock_db.add.call_count >= 1


@pytest.mark.unit
class TestNotifyApproved:
    """测试 notify_approved 方法"""

    def test_notify_approved_success(self):
        """测试审批通过通知"""
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.business_key = "TEST-001"

        mock_node = MagicMock()
        mock_node.id = 10

        mock_task = MagicMock()
        mock_task.id = 100
        mock_task.assignee_id = 50

        service.notify_approved(mock_instance, mock_node, mock_task, extra_context=None)

        assert mock_db.add.call_count >= 1

    def test_notify_approved_with_extra_context(self):
        """测试审批通过通知-带额外上下文"""
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.business_key = "TEST-001"

        mock_task = MagicMock()
        mock_task.id = 100
        mock_task.assignee_id = 50

        extra_context = {"custom_field": "value"}

        service.notify_approved(
        mock_instance, mock_node, mock_task, extra_context=extra_context
        )

        assert mock_db.add.call_count >= 1


@pytest.mark.unit
class TestNotifyRejected:
    """测试 notify_rejected 方法"""

    def test_notify_rejected_success(self):
        """测试审批拒绝通知"""
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.business_key = "TEST-001"

        mock_task = MagicMock()
        mock_task.id = 100
        mock_task.assignee_id = 50

        rejector_name = "张经理"

        service.notify_rejected(
        mock_instance,
        mock_node,
        mock_task,
        rejector_name=rejector_name,
        extra_context=None,
        )

        assert mock_db.add.call_count >= 1


@pytest.mark.unit
class TestNotifyCc:
    """测试 notify_cc 方法"""

    def test_notify_cc_success(self):
        """测试抄送通知"""
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.business_key = "TEST-001"

        mock_node = MagicMock()
        mock_node.id = 10

        cc_user_ids = [100, 200, 300]

        service.notify_cc(mock_instance, mock_node, cc_user_ids, extra_context=None)

        assert mock_db.add.call_count >= 3


@pytest.mark.unit
class TestNotifyTimeoutWarning:
    """测试 notify_timeout_warning 方法"""

    def test_notify_timeout_warning_success(self):
        """测试超时警告通知"""
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 1

        mock_task = MagicMock()
        mock_task.id = 100
        mock_task.assignee_id = 50

        service.notify_timeout_warning(
        mock_instance, mock_task, hours_remaining=24, extra_context=None
        )

        assert mock_db.add.call_count >= 1


@pytest.mark.unit
class TestGenerateDedupKey:
    """测试 _generate_dedup_key 方法"""

    def test_generate_dedup_key(self):
        """测试生成去重key"""
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)

        notification = {
        "instance_id": 1,
        "node_id": 10,
        "task_id": 100,
        "type": "APPROVED",
        "recipient_id": 50,
        }

        key = service._generate_dedup_key(notification)

        expected_key = "1:10:100:APPROVED:50"
        assert key == expected_key

    def test_is_duplicate_true(self):
        """测试重复检测-有重复"""
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)

        with patch.object(
        service, "_check_user_preferences", return_value={"dedup_window_hours": 1}
        ):
        is_dup = service._is_duplicate("1:10:100:APPROVED:50")
        assert is_dup is True

    def test_is_duplicate_false(self):
        """测试重复检测-无重复"""
        mock_db = MagicMock()
        service = ApprovalNotifyService(db=mock_db)

        with patch.object(
        service, "_check_user_preferences", return_value={"dedup_window_hours": 0}
        ):
        is_dup = service._is_duplicate("1:10:100:APPROVED:50")
        assert is_dup is False


@pytest.mark.unit
class TestNotifyServiceIntegration:
    """集成测试"""

    def test_all_methods_callable(self):
        """测试所有公共方法可调用"""
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
