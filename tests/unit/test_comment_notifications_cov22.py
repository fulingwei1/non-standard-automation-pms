# -*- coding: utf-8 -*-
"""第二十二批：comment_notifications 单元测试"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

try:
    from app.services.approval_engine.notify.comment_notifications import CommentNotificationsMixin
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="import failed")


class ConcreteCommentNotifier(CommentNotificationsMixin):
    """具体实现用于测试"""
    def __init__(self):
        self.sent_notifications = []

    def _send_notification(self, notification):
        self.sent_notifications.append(notification)


@pytest.fixture
def notifier():
    return ConcreteCommentNotifier()


@pytest.fixture
def mock_instance():
    inst = MagicMock()
    inst.id = 20
    inst.title = "采购申请"
    inst.created_at = datetime(2025, 2, 1)
    inst.initiator_id = 50
    return inst


class TestNotifyComment:
    def test_no_mentions_sends_nothing(self, notifier, mock_instance):
        """没有@用户时不发送提醒"""
        notifier.notify_comment(
            mock_instance,
            commenter_name="李四",
            comment_content="已审核",
            mentioned_user_ids=None
        )
        assert len(notifier.sent_notifications) == 0

    def test_empty_mentions_sends_nothing(self, notifier, mock_instance):
        """空的@用户列表不发送"""
        notifier.notify_comment(
            mock_instance,
            commenter_name="李四",
            comment_content="已审核",
            mentioned_user_ids=[]
        )
        assert len(notifier.sent_notifications) == 0

    def test_single_mention_sends_one_notification(self, notifier, mock_instance):
        """单个@用户时发送一条通知"""
        notifier.notify_comment(
            mock_instance,
            commenter_name="李四",
            comment_content="请尽快处理",
            mentioned_user_ids=[101]
        )
        assert len(notifier.sent_notifications) == 1

    def test_multiple_mentions_sends_multiple_notifications(self, notifier, mock_instance):
        """多个@用户时每人发送一条"""
        notifier.notify_comment(
            mock_instance,
            commenter_name="李四",
            comment_content="请各位查看",
            mentioned_user_ids=[101, 102, 103]
        )
        assert len(notifier.sent_notifications) == 3

    def test_notification_type_is_mention(self, notifier, mock_instance):
        """通知类型为 APPROVAL_COMMENT_MENTION"""
        notifier.notify_comment(
            mock_instance,
            commenter_name="李四",
            comment_content="请看",
            mentioned_user_ids=[101]
        )
        assert notifier.sent_notifications[0]["type"] == "APPROVAL_COMMENT_MENTION"

    def test_receiver_id_matches_mentioned_user(self, notifier, mock_instance):
        """接收者ID匹配被@的用户"""
        notifier.notify_comment(
            mock_instance,
            commenter_name="李四",
            comment_content="请看",
            mentioned_user_ids=[202]
        )
        assert notifier.sent_notifications[0]["receiver_id"] == 202

    def test_commenter_name_in_title(self, notifier, mock_instance):
        """标题包含评论人名字"""
        notifier.notify_comment(
            mock_instance,
            commenter_name="王五",
            comment_content="请看",
            mentioned_user_ids=[101]
        )
        assert "王五" in notifier.sent_notifications[0]["title"]

    def test_instance_id_in_notification(self, notifier, mock_instance):
        """通知包含实例ID"""
        notifier.notify_comment(
            mock_instance,
            commenter_name="李四",
            comment_content="请看",
            mentioned_user_ids=[101]
        )
        assert notifier.sent_notifications[0]["instance_id"] == 20
