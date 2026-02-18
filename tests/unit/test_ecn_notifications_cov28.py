# -*- coding: utf-8 -*-
"""第二十八批 - ecn_notifications 单元测试"""

import pytest
from unittest.mock import MagicMock, call, patch

pytest.importorskip("app.services.ecn_notification.ecn_notifications")

from app.services.ecn_notification.ecn_notifications import (
    notify_ecn_submitted,
    notify_overdue_alert,
)


# ─── 辅助工厂 ───────────────────────────────────────────────

def _make_ecn(
    ecn_id=1,
    ecn_no="ECN-2024-001",
    ecn_title="变更测试",
    applicant_id=10,
    project_id=None,
    ecn_type="设计变更",
    change_reason="客户需求",
):
    ecn = MagicMock()
    ecn.id = ecn_id
    ecn.ecn_no = ecn_no
    ecn.ecn_title = ecn_title
    ecn.applicant_id = applicant_id
    ecn.project_id = project_id
    ecn.ecn_type = ecn_type
    ecn.change_reason = change_reason
    return ecn


def _make_alert(ecn_id=1, ecn_no="ECN-001", overdue_days=3, message="超时提醒"):
    return {
        "ecn_id": ecn_id,
        "ecn_no": ecn_no,
        "overdue_days": overdue_days,
        "message": message,
        "type": "OVERDUE",
    }


# ─── notify_ecn_submitted ────────────────────────────────────

class TestNotifyEcnSubmitted:

    @patch("app.services.ecn_notification.ecn_notifications.NotificationDispatcher")
    def test_notifies_applicant_when_present(self, mock_dispatcher_cls):
        """有申请人时应发送提交通知"""
        db = MagicMock()
        dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = dispatcher

        ecn = _make_ecn(applicant_id=5, project_id=None)
        notify_ecn_submitted(db, ecn)

        mock_dispatcher_cls.assert_called_once_with(db)
        dispatcher.send_notification_request.assert_called_once()
        req = dispatcher.send_notification_request.call_args[0][0]
        assert req.recipient_id == 5
        assert req.notification_type == "ECN_SUBMITTED"
        assert "ECN-2024-001" in req.title

    @patch("app.services.ecn_notification.ecn_notifications.NotificationDispatcher")
    def test_no_applicant_skips_applicant_notification(self, mock_dispatcher_cls):
        """没有申请人时不发申请人通知"""
        db = MagicMock()
        dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = dispatcher

        ecn = _make_ecn(applicant_id=None, project_id=None)
        notify_ecn_submitted(db, ecn)

        dispatcher.send_notification_request.assert_not_called()

    @patch("app.services.ecn_notification.ecn_notifications.NotificationDispatcher")
    def test_notifies_project_members_when_project_exists(self, mock_dispatcher_cls):
        """有关联项目时应通知项目成员（排除申请人）"""
        db = MagicMock()
        dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = dispatcher

        member1 = MagicMock()
        member1.user_id = 20
        member2 = MagicMock()
        member2.user_id = 21
        db.query.return_value.filter.return_value.all.return_value = [member1, member2]

        ecn = _make_ecn(applicant_id=10, project_id=3)
        notify_ecn_submitted(db, ecn)

        # 1次申请人 + 2次项目成员 = 3次
        assert dispatcher.send_notification_request.call_count == 3

    @patch("app.services.ecn_notification.ecn_notifications.NotificationDispatcher")
    def test_no_project_members_skips_cc(self, mock_dispatcher_cls):
        """项目成员为空时不发抄送通知"""
        db = MagicMock()
        dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = dispatcher

        db.query.return_value.filter.return_value.all.return_value = []

        ecn = _make_ecn(applicant_id=10, project_id=5)
        notify_ecn_submitted(db, ecn)

        # 只发申请人通知
        assert dispatcher.send_notification_request.call_count == 1

    @patch("app.services.ecn_notification.ecn_notifications.NotificationDispatcher")
    def test_cc_request_has_is_cc_flag(self, mock_dispatcher_cls):
        """抄送通知的 extra_data 应包含 is_cc=True"""
        db = MagicMock()
        dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = dispatcher

        member = MagicMock()
        member.user_id = 30
        db.query.return_value.filter.return_value.all.return_value = [member]

        ecn = _make_ecn(applicant_id=10, project_id=2)
        notify_ecn_submitted(db, ecn)

        calls = dispatcher.send_notification_request.call_args_list
        # 第二个调用是抄送
        cc_req = calls[1][0][0]
        assert cc_req.extra_data.get("is_cc") is True

    @patch("app.services.ecn_notification.ecn_notifications.NotificationDispatcher")
    def test_notification_link_url_contains_ecn_id(self, mock_dispatcher_cls):
        """通知链接应包含 ECN ID"""
        db = MagicMock()
        dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = dispatcher

        ecn = _make_ecn(ecn_id=42, applicant_id=5, project_id=None)
        notify_ecn_submitted(db, ecn)

        req = dispatcher.send_notification_request.call_args[0][0]
        assert "42" in req.link_url


# ─── notify_overdue_alert ────────────────────────────────────

class TestNotifyOverdueAlert:

    @patch("app.services.ecn_notification.ecn_notifications.NotificationDispatcher")
    def test_sends_to_each_user(self, mock_dispatcher_cls):
        """应向每个 user_id 发送通知"""
        db = MagicMock()
        dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = dispatcher

        alert = _make_alert(overdue_days=3)
        notify_overdue_alert(db, alert, user_ids=[1, 2, 3])

        assert dispatcher.send_notification_request.call_count == 3

    @patch("app.services.ecn_notification.ecn_notifications.NotificationDispatcher")
    def test_empty_user_ids_sends_nothing(self, mock_dispatcher_cls):
        """用户列表为空时不发送通知"""
        db = MagicMock()
        dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = dispatcher

        alert = _make_alert()
        notify_overdue_alert(db, alert, user_ids=[])

        dispatcher.send_notification_request.assert_not_called()

    @patch("app.services.ecn_notification.ecn_notifications.NotificationDispatcher")
    def test_urgent_priority_when_overdue_gt_7(self, mock_dispatcher_cls):
        """超过 7 天应使用 URGENT 优先级"""
        from app.services.channel_handlers.base import NotificationPriority

        db = MagicMock()
        dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = dispatcher

        alert = _make_alert(overdue_days=10)
        notify_overdue_alert(db, alert, user_ids=[1])

        req = dispatcher.send_notification_request.call_args[0][0]
        assert req.priority == NotificationPriority.URGENT

    @patch("app.services.ecn_notification.ecn_notifications.NotificationDispatcher")
    def test_high_priority_when_overdue_le_7(self, mock_dispatcher_cls):
        """不超过 7 天应使用 HIGH 优先级"""
        from app.services.channel_handlers.base import NotificationPriority

        db = MagicMock()
        dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = dispatcher

        alert = _make_alert(overdue_days=5)
        notify_overdue_alert(db, alert, user_ids=[1])

        req = dispatcher.send_notification_request.call_args[0][0]
        assert req.priority == NotificationPriority.HIGH

    @patch("app.services.ecn_notification.ecn_notifications.NotificationDispatcher")
    def test_notification_type_is_ecn_overdue(self, mock_dispatcher_cls):
        """通知类型应为 ECN_OVERDUE_ALERT"""
        db = MagicMock()
        dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = dispatcher

        alert = _make_alert()
        notify_overdue_alert(db, alert, user_ids=[1])

        req = dispatcher.send_notification_request.call_args[0][0]
        assert req.notification_type == "ECN_OVERDUE_ALERT"

    @patch("app.services.ecn_notification.ecn_notifications.NotificationDispatcher")
    def test_extra_data_contains_overdue_days(self, mock_dispatcher_cls):
        """extra_data 应包含 overdue_days 字段"""
        db = MagicMock()
        dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = dispatcher

        alert = _make_alert(overdue_days=4)
        notify_overdue_alert(db, alert, user_ids=[7])

        req = dispatcher.send_notification_request.call_args[0][0]
        assert req.extra_data["overdue_days"] == 4

    @patch("app.services.ecn_notification.ecn_notifications.NotificationDispatcher")
    def test_link_url_is_none_when_no_ecn_id(self, mock_dispatcher_cls):
        """没有 ecn_id 时 link_url 应为 None"""
        db = MagicMock()
        dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = dispatcher

        alert = {"ecn_no": "ECN-X", "overdue_days": 2, "message": "msg", "type": "OVERDUE"}
        notify_overdue_alert(db, alert, user_ids=[1])

        req = dispatcher.send_notification_request.call_args[0][0]
        assert req.link_url is None
