# -*- coding: utf-8 -*-
"""evaluation_notifications 单元测试"""
from unittest.mock import MagicMock, patch
import pytest

from app.services.ecn_notification.evaluation_notifications import (
    notify_evaluation_assigned,
    notify_evaluation_completed,
)


class TestNotifyEvaluationAssigned:
    @patch("app.services.ecn_notification.evaluation_notifications.NotificationDispatcher")
    @patch("app.services.ecn_notification.evaluation_notifications.find_users_by_department")
    @patch("app.services.ecn_notification.evaluation_notifications.find_department_manager")
    def test_no_evaluator(self, mock_mgr, mock_find, mock_disp):
        mock_find.return_value = []
        mock_mgr.return_value = None
        db = MagicMock()
        ecn = MagicMock()
        evaluation = MagicMock()
        evaluation.eval_dept = "ENG"
        notify_evaluation_assigned(db, ecn, evaluation)
        mock_disp.return_value.send_notification_request.assert_not_called()

    @patch("app.services.ecn_notification.evaluation_notifications.NotificationDispatcher")
    def test_with_evaluator(self, mock_disp):
        db = MagicMock()
        user = MagicMock()
        user.id = 5
        db.query.return_value.filter.return_value.first.return_value = user
        ecn = MagicMock()
        ecn.ecn_no = "ECN001"
        ecn.ecn_title = "Test"
        ecn.id = 1
        evaluation = MagicMock()
        evaluation.eval_dept = "ENG"
        evaluation.id = 10
        notify_evaluation_assigned(db, ecn, evaluation, evaluator_id=5)
        mock_disp.return_value.send_notification_request.assert_called_once()


class TestNotifyEvaluationCompleted:
    @patch("app.services.ecn_notification.evaluation_notifications.check_all_evaluations_completed", return_value=False)
    @patch("app.services.ecn_notification.evaluation_notifications.NotificationDispatcher")
    def test_notify_applicant(self, mock_disp, mock_check):
        db = MagicMock()
        ecn = MagicMock()
        ecn.applicant_id = 1
        ecn.ecn_no = "ECN001"
        ecn.id = 1
        ecn.project_id = None
        evaluation = MagicMock()
        evaluation.eval_dept = "ENG"
        evaluation.eval_result = "OK"
        evaluation.cost_estimate = 1000
        evaluation.schedule_estimate = 5
        notify_evaluation_completed(db, ecn, evaluation)
        mock_disp.return_value.send_notification_request.assert_called()
