# -*- coding: utf-8 -*-
"""
审批通知服务 - 批量通知 单元测试 (Batch 19)

测试 app/services/approval_engine/notify/batch.py
覆盖率目标: 60%+
"""

from unittest.mock import MagicMock, call

import pytest

from app.services.approval_engine.notify.batch import BatchNotificationMixin


@pytest.mark.unit
class TestBatchNotificationMixin:
    """测试批量通知功能"""

    def test_batch_notify_empty_list(self):
        """测试空通知列表"""
        mixin = BatchNotificationMixin()
        mixin._send_notification = MagicMock()

        mixin.batch_notify([])

        mixin._send_notification.assert_not_called()

    def test_batch_notify_single_notification(self):
        """测试单个通知"""
        mixin = BatchNotificationMixin()
        mixin._send_notification = MagicMock()

        notifications = [
            {
                "user_id": 100,
                "title": "审批通知",
                "content": "您有新的审批任务",
            }
        ]

        mixin.batch_notify(notifications)

        mixin._send_notification.assert_called_once_with(notifications[0])

    def test_batch_notify_multiple_notifications(self):
        """测试多个通知"""
        mixin = BatchNotificationMixin()
        mixin._send_notification = MagicMock()

        notifications = [
            {
                "user_id": 100,
                "title": "审批通知1",
                "content": "内容1",
            },
            {
                "user_id": 200,
                "title": "审批通知2",
                "content": "内容2",
            },
            {
                "user_id": 300,
                "title": "审批通知3",
                "content": "内容3",
            },
        ]

        mixin.batch_notify(notifications)

        # 验证调用次数
        assert mixin._send_notification.call_count == 3

        # 验证每个通知都被调用
        expected_calls = [call(n) for n in notifications]
        mixin._send_notification.assert_has_calls(expected_calls)

    def test_batch_notify_different_types(self):
        """测试不同类型的通知"""
        mixin = BatchNotificationMixin()
        mixin._send_notification = MagicMock()

        notifications = [
            {
                "user_id": 100,
                "type": "EMAIL",
                "title": "邮件通知",
            },
            {
                "user_id": 200,
                "type": "SMS",
                "title": "短信通知",
            },
            {
                "user_id": 300,
                "type": "PUSH",
                "title": "推送通知",
            },
        ]

        mixin.batch_notify(notifications)

        assert mixin._send_notification.call_count == 3

    def test_batch_notify_with_error_handling(self):
        """测试发送失败时继续处理其他通知"""
        mixin = BatchNotificationMixin()

        # 模拟第2个通知发送失败
        def send_with_error(notification):
            if notification["user_id"] == 200:
                raise Exception("发送失败")

        mixin._send_notification = MagicMock(side_effect=send_with_error)

        notifications = [
            {"user_id": 100, "title": "通知1"},
            {"user_id": 200, "title": "通知2"},  # 会失败
            {"user_id": 300, "title": "通知3"},
        ]

        # 批量发送应该抛出异常（因为没有错误处理）
        with pytest.raises(Exception, match="发送失败"):
            mixin.batch_notify(notifications)

        # 验证前两个通知被尝试发送
        assert mixin._send_notification.call_count == 2

    def test_batch_notify_large_batch(self):
        """测试大批量通知"""
        mixin = BatchNotificationMixin()
        mixin._send_notification = MagicMock()

        # 创建100个通知
        notifications = [
            {
                "user_id": i,
                "title": f"通知{i}",
                "content": f"内容{i}",
            }
            for i in range(1, 101)
        ]

        mixin.batch_notify(notifications)

        # 验证所有通知都被发送
        assert mixin._send_notification.call_count == 100

    def test_batch_notify_preserves_order(self):
        """测试保持发送顺序"""
        mixin = BatchNotificationMixin()
        sent_order = []

        def track_order(notification):
            sent_order.append(notification["user_id"])

        mixin._send_notification = MagicMock(side_effect=track_order)

        notifications = [
            {"user_id": 5, "title": "A"},
            {"user_id": 3, "title": "B"},
            {"user_id": 7, "title": "C"},
            {"user_id": 1, "title": "D"},
        ]

        mixin.batch_notify(notifications)

        # 验证发送顺序与输入顺序一致
        assert sent_order == [5, 3, 7, 1]

    def test_batch_notify_with_complex_payload(self):
        """测试复杂通知数据"""
        mixin = BatchNotificationMixin()
        mixin._send_notification = MagicMock()

        notifications = [
            {
                "user_id": 100,
                "title": "复杂通知",
                "content": "内容",
                "metadata": {
                    "instance_id": 123,
                    "task_id": 456,
                    "urgency": "HIGH",
                },
                "attachments": [
                    {"name": "file1.pdf", "url": "http://..."},
                    {"name": "file2.doc", "url": "http://..."},
                ],
                "actions": [
                    {"type": "APPROVE", "label": "同意"},
                    {"type": "REJECT", "label": "驳回"},
                ],
            }
        ]

        mixin.batch_notify(notifications)

        # 验证完整数据被传递
        mixin._send_notification.assert_called_once()
        sent_notification = mixin._send_notification.call_args[0][0]
        assert sent_notification["metadata"]["instance_id"] == 123
        assert len(sent_notification["attachments"]) == 2
        assert len(sent_notification["actions"]) == 2

    def test_batch_notify_none_values(self):
        """测试包含None值的通知"""
        mixin = BatchNotificationMixin()
        mixin._send_notification = MagicMock()

        notifications = [
            {
                "user_id": 100,
                "title": "通知",
                "content": None,  # 内容为空
                "metadata": None,  # 元数据为空
            }
        ]

        mixin.batch_notify(notifications)

        mixin._send_notification.assert_called_once()

    def test_batch_notify_duplicate_users(self):
        """测试同一用户收到多个通知"""
        mixin = BatchNotificationMixin()
        mixin._send_notification = MagicMock()

        # 同一用户收到3个通知
        notifications = [
            {"user_id": 100, "title": "通知1"},
            {"user_id": 100, "title": "通知2"},
            {"user_id": 100, "title": "通知3"},
        ]

        mixin.batch_notify(notifications)

        # 应该发送3次（不去重）
        assert mixin._send_notification.call_count == 3
