# -*- coding: utf-8 -*-
"""评论通知单元测试"""
import pytest
from unittest.mock import MagicMock
from app.services.approval_engine.notify.comment_notifications import CommentNotificationsMixin


class TestCommentNotificationsMixin:
    def setup_method(self):
        self.mixin = CommentNotificationsMixin()
        self.mixin._send_notification = MagicMock()

    def test_notify_comment_with_mentions(self):
        instance = MagicMock()
        instance.title = "测试审批"
        instance.id = 1
        self.mixin.notify_comment(instance, "张三", "请看一下", [10, 20])
        assert self.mixin._send_notification.call_count == 2

    def test_notify_comment_no_mentions(self):
        instance = MagicMock()
        instance.title = "测试审批"
        instance.id = 1
        self.mixin.notify_comment(instance, "张三", "一般评论", None)
        self.mixin._send_notification.assert_not_called()

    def test_notify_comment_content_truncated(self):
        instance = MagicMock()
        instance.title = "测试审批"
        instance.id = 1
        long_content = "x" * 200
        self.mixin.notify_comment(instance, "张三", long_content, [10])
        notification = self.mixin._send_notification.call_args[0][0]
        assert len(notification["content"]) < 200
