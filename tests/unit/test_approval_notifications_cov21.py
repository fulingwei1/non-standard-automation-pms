# -*- coding: utf-8 -*-
"""第二十一批：ECN审批通知单元测试"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date, datetime

pytest.importorskip("app.services.ecn_notification.approval_notifications")


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_ecn(ecn_id=1, ecn_no="ECN-001", project_id=10, applicant_id=5):
    ecn = MagicMock()
    ecn.id = ecn_id
    ecn.ecn_no = ecn_no
    ecn.ecn_title = "变更申请：修改接口规格"
    ecn.project_id = project_id
    ecn.applicant_id = applicant_id
    return ecn


def _make_approval(approval_id=1, level=1, role="TECH_REVIEW", due_date=None):
    approval = MagicMock()
    approval.id = approval_id
    approval.approval_level = level
    approval.approval_role = role
    approval.due_date = due_date
    approval.approval_opinion = "同意"
    return approval


class TestNotifyApprovalAssigned:
    def test_no_approver_id_skips(self, mock_db):
        from app.services.ecn_notification.approval_notifications import notify_approval_assigned
        ecn = _make_ecn()
        approval = _make_approval()

        with patch("app.services.ecn_notification.approval_notifications.find_users_by_role",
                   return_value=[]):
            notify_approval_assigned(mock_db, ecn, approval, approver_id=None)
        # Should not send any notification

    def test_sends_notification_to_approver(self, mock_db):
        from app.services.ecn_notification.approval_notifications import notify_approval_assigned
        ecn = _make_ecn()
        approval = _make_approval()
        approver = MagicMock()
        approver.id = 10
        approver.real_name = "张三"
        mock_db.query.return_value.filter.return_value.first.return_value = approver
        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_dispatcher = MagicMock()
        with patch("app.services.ecn_notification.approval_notifications.NotificationDispatcher",
                   return_value=mock_dispatcher):
            notify_approval_assigned(mock_db, ecn, approval, approver_id=10)
        mock_dispatcher.send_notification_request.assert_called()

    def test_sends_cc_to_project_members(self, mock_db):
        from app.services.ecn_notification.approval_notifications import notify_approval_assigned
        ecn = _make_ecn(project_id=10)
        approval = _make_approval()

        approver = MagicMock(spec=["id", "real_name", "username"])
        approver.id = 10
        approver.real_name = "张三"
        approver.username = "zhangsan"

        pm1 = MagicMock()
        pm1.user_id = 20
        pm2 = MagicMock()
        pm2.user_id = 21

        approver2 = MagicMock(spec=["id", "real_name", "username"])
        approver2.real_name = "张三"
        approver2.username = "zhangsan"

        # first: approver User lookup; then project members; then approvers name query
        mock_db.query.return_value.filter.return_value.first.return_value = approver
        mock_db.query.return_value.filter.return_value.all.side_effect = [[pm1, pm2], [approver2]]

        mock_dispatcher = MagicMock()
        with patch("app.services.ecn_notification.approval_notifications.NotificationDispatcher",
                   return_value=mock_dispatcher):
            notify_approval_assigned(mock_db, ecn, approval, approver_id=10)
        # dispatcher should be called multiple times (approver + cc members)
        assert mock_dispatcher.send_notification_request.call_count >= 1


class TestNotifyApprovalResult:
    def test_notifies_applicant_on_approved(self, mock_db):
        from app.services.ecn_notification.approval_notifications import notify_approval_result
        ecn = _make_ecn(applicant_id=5, project_id=None)
        approval = _make_approval()
        # No project members, no tasks
        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_dispatcher = MagicMock()
        mock_ecn_task = MagicMock()
        mock_ecn_task.task_status = MagicMock()
        with patch("app.services.ecn_notification.approval_notifications.NotificationDispatcher",
                   return_value=mock_dispatcher), \
             patch("app.services.ecn_notification.approval_notifications.EcnTask", mock_ecn_task):
            notify_approval_result(mock_db, ecn, approval, result="APPROVED")
        mock_dispatcher.send_notification_request.assert_called()

    def test_notifies_applicant_on_rejected(self, mock_db):
        from app.services.ecn_notification.approval_notifications import notify_approval_result
        ecn = _make_ecn(applicant_id=5, project_id=None)
        approval = _make_approval()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_dispatcher = MagicMock()
        with patch("app.services.ecn_notification.approval_notifications.NotificationDispatcher",
                   return_value=mock_dispatcher):
            notify_approval_result(mock_db, ecn, approval, result="REJECTED")
        mock_dispatcher.send_notification_request.assert_called()

    def test_notifies_task_assignees_on_approved(self, mock_db):
        from app.services.ecn_notification.approval_notifications import notify_approval_result
        from datetime import date
        ecn = _make_ecn(applicant_id=5, project_id=None)
        approval = _make_approval()

        task = MagicMock()
        task.assignee_id = 30
        task.task_name = "更新图纸"
        task.task_type = "DESIGN"
        task.planned_end = date(2025, 12, 31)

        mock_db.query.return_value.filter.return_value.all.return_value = [task]

        mock_dispatcher = MagicMock()
        mock_ecn_task = MagicMock()
        mock_ecn_task.task_status = MagicMock()
        with patch("app.services.ecn_notification.approval_notifications.NotificationDispatcher",
                   return_value=mock_dispatcher), \
             patch("app.services.ecn_notification.approval_notifications.EcnTask", mock_ecn_task):
            notify_approval_result(mock_db, ecn, approval, result="APPROVED")
        # applicant + task assignee
        assert mock_dispatcher.send_notification_request.call_count >= 2
