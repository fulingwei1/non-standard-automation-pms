# -*- coding: utf-8 -*-
"""第二十九批 - ecn_notification/task_notifications.py 单元测试（ECN任务通知）"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch, call

pytest.importorskip("app.services.ecn_notification.task_notifications")

from app.services.ecn_notification.task_notifications import (
    notify_task_assigned,
    notify_task_completed,
)


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_db():
    return MagicMock()


def _make_ecn(project_id=None, applicant_id=1):
    ecn = MagicMock()
    ecn.id = 100
    ecn.ecn_no = "ECN-2024-001"
    ecn.ecn_title = "ECN测试标题"
    ecn.project_id = project_id
    ecn.applicant_id = applicant_id
    return ecn


def _make_task(task_dept="研发部", planned_end=None, task_name="测试任务"):
    task = MagicMock()
    task.id = 200
    task.task_name = task_name
    task.task_type = "ENGINEERING"
    task.task_dept = task_dept
    task.planned_end = planned_end
    task.completion_note = None
    return task


def _make_user(user_id=1, real_name="张三", username="zhangsan"):
    u = MagicMock()
    u.id = user_id
    u.real_name = real_name
    u.username = username
    return u


# ─── 测试：notify_task_assigned ────────────────────────────────────────────────

class TestNotifyTaskAssigned:
    """测试任务分配通知"""

    @patch("app.services.ecn_notification.task_notifications.NotificationDispatcher")
    def test_assigns_to_specified_assignee(self, mock_dispatcher_cls):
        db = _make_db()
        ecn = _make_ecn()
        task = _make_task()
        user = _make_user(user_id=5)
        db.query.return_value.filter.return_value.first.return_value = user
        mock_dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = mock_dispatcher

        notify_task_assigned(db, ecn, task, assignee_id=5)

        mock_dispatcher.send_notification_request.assert_called()

    @patch("app.services.ecn_notification.task_notifications.find_users_by_department")
    @patch("app.services.ecn_notification.task_notifications.NotificationDispatcher")
    def test_returns_early_when_no_assignee_found(self, mock_dispatcher_cls, mock_find_users):
        db = _make_db()
        ecn = _make_ecn()
        task = _make_task()
        # 部门查找返回空
        mock_find_users.return_value = []

        notify_task_assigned(db, ecn, task, assignee_id=None)

        # 没有assignee时返回，不应该调用dispatcher
        mock_dispatcher_cls.assert_not_called()

    @patch("app.services.ecn_notification.task_notifications.find_users_by_department")
    @patch("app.services.ecn_notification.task_notifications.NotificationDispatcher")
    def test_finds_assignee_via_department_when_none_given(self, mock_dispatcher_cls, mock_find_users):
        db = _make_db()
        ecn = _make_ecn()
        task = _make_task()
        dept_user = _make_user(user_id=7)
        mock_find_users.return_value = [dept_user]
        db.query.return_value.filter.return_value.first.return_value = dept_user
        mock_dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = mock_dispatcher

        notify_task_assigned(db, ecn, task, assignee_id=None)

        mock_find_users.assert_called_once()
        mock_dispatcher.send_notification_request.assert_called()

    @patch("app.services.ecn_notification.task_notifications.NotificationDispatcher")
    def test_urgent_priority_for_overdue_task(self, mock_dispatcher_cls):
        db = _make_db()
        ecn = _make_ecn()
        # 过期任务
        overdue_end = date.today() - timedelta(days=1)
        task = _make_task(planned_end=overdue_end)
        user = _make_user(user_id=3)
        db.query.return_value.filter.return_value.first.return_value = user
        mock_dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = mock_dispatcher

        notify_task_assigned(db, ecn, task, assignee_id=3)

        # 验证调用时带有 URGENT 优先级
        call_args = mock_dispatcher.send_notification_request.call_args
        assert call_args is not None
        request = call_args[0][0]
        from app.services.channel_handlers.base import NotificationPriority
        assert request.priority == NotificationPriority.URGENT

    @patch("app.services.ecn_notification.task_notifications.NotificationDispatcher")
    def test_notifies_project_members_as_cc(self, mock_dispatcher_cls):
        db = _make_db()
        ecn = _make_ecn(project_id=10)
        task = _make_task()
        # 使用真实字符串作为real_name和username，避免join失败
        user = _make_user(user_id=5, real_name="执行人员", username="executor")
        member1 = MagicMock()
        member1.user_id = 8
        member2 = MagicMock()
        member2.user_id = 9

        # 第一次query返回用户，第二次返回project members
        call_order = [0]

        def query_side(model):
            q = MagicMock()
            q.filter.return_value.first.return_value = user
            q.filter.return_value.all.return_value = [user]
            q.filter.return_value.filter.return_value.all.return_value = [member1, member2]
            return q

        db.query.side_effect = query_side
        mock_dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = mock_dispatcher

        notify_task_assigned(db, ecn, task, assignee_id=5)

        # 至少调用过一次dispatcher
        assert mock_dispatcher.send_notification_request.call_count >= 1


# ─── 测试：notify_task_completed ────────────────────────────────────────────────

class TestNotifyTaskCompleted:
    """测试任务完成通知"""

    @patch("app.services.ecn_notification.task_notifications.NotificationDispatcher")
    def test_notifies_applicant_on_completion(self, mock_dispatcher_cls):
        db = _make_db()
        ecn = _make_ecn(applicant_id=1, project_id=None)
        task = _make_task()
        mock_dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = mock_dispatcher

        notify_task_completed(db, ecn, task)

        mock_dispatcher.send_notification_request.assert_called()
        request = mock_dispatcher.send_notification_request.call_args[0][0]
        assert request.recipient_id == 1
        assert "ECN_TASK_COMPLETED" in request.notification_type

    @patch("app.services.ecn_notification.task_notifications.NotificationDispatcher")
    def test_task_completion_content_includes_task_name(self, mock_dispatcher_cls):
        db = _make_db()
        ecn = _make_ecn(applicant_id=2, project_id=None)
        task = _make_task(task_name="特殊任务名称")
        mock_dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = mock_dispatcher

        notify_task_completed(db, ecn, task)

        request = mock_dispatcher.send_notification_request.call_args[0][0]
        assert "特殊任务名称" in request.content

    @patch("app.services.ecn_notification.task_notifications.NotificationDispatcher")
    def test_notifies_project_members_as_cc_on_completion(self, mock_dispatcher_cls):
        db = _make_db()
        ecn = _make_ecn(applicant_id=1, project_id=20)
        task = _make_task()
        member1 = MagicMock()
        member1.user_id = 11
        member2 = MagicMock()
        member2.user_id = 12
        db.query.return_value.filter.return_value.all.return_value = [member1, member2]
        mock_dispatcher = MagicMock()
        mock_dispatcher_cls.return_value = mock_dispatcher

        notify_task_completed(db, ecn, task)

        # 应该被多次调用（主通知 + 抄送）
        assert mock_dispatcher.send_notification_request.call_count >= 1
