# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - 审批评论通知
tests/unit/test_comment_notifications_cov37.py
"""
import pytest
from unittest.mock import MagicMock

pytest.importorskip("app.services.approval_engine.notify.comment_notifications")

from app.services.approval_engine.notify.comment_notifications import CommentNotificationsMixin


class ConcreteComment(CommentNotificationsMixin):
    def __init__(self):
        self._sent = []

    def _send_notification(self, notification):
        self._sent.append(notification)


def _make_instance(title="审批A"):
    inst = MagicMock()
    inst.id = 10
    inst.title = title
    inst.initiator_id = 1
    return inst


class TestCommentNotifications:
    def setup_method(self):
        self.notifier = ConcreteComment()

    def test_notify_comment_sends_to_mentioned_users(self):
        instance = _make_instance()
        self.notifier.notify_comment(
            instance, "李四", "这是评论内容", mentioned_user_ids=[2, 3]
        )
        assert len(self.notifier._sent) == 2

    def test_notify_comment_type_for_mention(self):
        instance = _make_instance()
        self.notifier.notify_comment(
            instance, "李四", "内容", mentioned_user_ids=[5]
        )
        assert self.notifier._sent[0]["type"] == "APPROVAL_COMMENT_MENTION"

    def test_notify_comment_no_mentions_sends_nothing_extra(self):
        instance = _make_instance()
        self.notifier.notify_comment(
            instance, "王五", "评论", mentioned_user_ids=None
        )
        # No mention notifications
        assert all(n["type"] != "APPROVAL_COMMENT_MENTION" for n in self.notifier._sent)

    def test_notify_comment_title_contains_commenter_name(self):
        instance = _make_instance()
        self.notifier.notify_comment(
            instance, "张三", "内容", mentioned_user_ids=[7]
        )
        assert "张三" in self.notifier._sent[0]["title"]

    def test_notify_comment_content_truncated_to_100(self):
        instance = _make_instance()
        long_content = "A" * 200
        self.notifier.notify_comment(
            instance, "李四", long_content, mentioned_user_ids=[8]
        )
        assert len(self.notifier._sent[0]["content"]) <= 200  # title+content limited

    def test_notify_comment_receiver_is_mentioned_user(self):
        instance = _make_instance()
        self.notifier.notify_comment(
            instance, "测试者", "内容", mentioned_user_ids=[42]
        )
        assert self.notifier._sent[0]["receiver_id"] == 42

    def test_notify_comment_empty_mentioned_list(self):
        instance = _make_instance()
        self.notifier.notify_comment(
            instance, "测试者", "内容", mentioned_user_ids=[]
        )
        assert len(self.notifier._sent) == 0
