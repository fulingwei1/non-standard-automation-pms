# -*- coding: utf-8 -*-
"""task_notifications 单元测试"""
from unittest.mock import MagicMock, patch
import pytest

from app.services.ecn_notification.task_notifications import (
    notify_task_assigned,
    notify_task_completed,
)


class TestNotifyTaskAssigned:
    @patch("app.services.ecn_notification.task_notifications.NotificationDispatcher")
    @patch("app.services.ecn_notification.task_notifications.find_users_by_department")
    def test_no_assignee_no_dept_users(self, mock_find, mock_disp):
        mock_find.return_value = []
        db = MagicMock()
        ecn = MagicMock()
        task = MagicMock()
        task.task_dept = "ENG"
        notify_task_assigned(db, ecn, task)
        mock_disp.return_value.send_notification_request.assert_not_called()

    @patch("app.services.ecn_notification.task_notifications.NotificationDispatcher")
    def test_with_assignee(self, mock_disp):
        db = MagicMock()
        user = MagicMock()
        user.id = 5
        db.query.return_value.filter.return_value.first.return_value = user
        ecn = MagicMock()
        ecn.ecn_no = "ECN001"
        ecn.ecn_title = "Test"
        ecn.id = 1
        ecn.project_id = None
        task = MagicMock()
        task.task_name = "Task1"
        task.task_type = "TYPE"
        task.task_dept = "ENG"
        task.planned_end = None
        task.id = 10
        notify_task_assigned(db, ecn, task, assignee_id=5)
        mock_disp.return_value.send_notification_request.assert_called_once()

    @patch("app.services.ecn_notification.task_notifications.NotificationDispatcher")
    def test_assignee_not_found(self, mock_disp):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        ecn = MagicMock()
        task = MagicMock()
        task.task_dept = "ENG"
        notify_task_assigned(db, ecn, task, assignee_id=999)
        mock_disp.return_value.send_notification_request.assert_not_called()


class TestNotifyTaskCompleted:
    @patch("app.services.ecn_notification.task_notifications.NotificationDispatcher")
    def test_notify_applicant(self, mock_disp):
        db = MagicMock()
        ecn = MagicMock()
        ecn.applicant_id = 1
        ecn.ecn_no = "ECN001"
        ecn.id = 1
        ecn.project_id = None
        task = MagicMock()
        task.task_name = "Task1"
        task.id = 10
        task.completion_note = "Done"
        notify_task_completed(db, ecn, task)
        mock_disp.return_value.send_notification_request.assert_called()
