# -*- coding: utf-8 -*-
"""第二十四批 - evaluation_notifications 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.ecn_notification.evaluation_notifications")

from app.services.ecn_notification.evaluation_notifications import (
    notify_evaluation_assigned,
    notify_evaluation_completed,
)


def _make_ecn(ecn_id=1, ecn_no="ECN-001", ecn_title="变更标题",
              applicant_id=10, project_id=None):
    ecn = MagicMock()
    ecn.id = ecn_id
    ecn.ecn_no = ecn_no
    ecn.ecn_title = ecn_title
    ecn.applicant_id = applicant_id
    ecn.project_id = project_id
    return ecn


def _make_evaluation(eval_id=1, eval_dept="机械部", eval_result="同意",
                     cost_estimate=5000, schedule_estimate=7):
    ev = MagicMock()
    ev.id = eval_id
    ev.eval_dept = eval_dept
    ev.eval_result = eval_result
    ev.cost_estimate = cost_estimate
    ev.schedule_estimate = schedule_estimate
    return ev


class TestNotifyEvaluationAssigned:
    @patch("app.services.ecn_notification.evaluation_notifications.NotificationDispatcher")
    @patch("app.services.ecn_notification.evaluation_notifications.find_users_by_department")
    @patch("app.services.ecn_notification.evaluation_notifications.find_department_manager")
    def test_sends_with_evaluator_id(self, mock_mgr, mock_dept, mock_dispatcher):
        db = MagicMock()
        user = MagicMock()
        user.id = 5
        db.query.return_value.filter.return_value.first.return_value = user

        dispatcher_instance = MagicMock()
        mock_dispatcher.return_value = dispatcher_instance

        ecn = _make_ecn()
        ev = _make_evaluation()
        notify_evaluation_assigned(db, ecn, ev, evaluator_id=5)

        dispatcher_instance.send_notification_request.assert_called_once()

    @patch("app.services.ecn_notification.evaluation_notifications.NotificationDispatcher")
    @patch("app.services.ecn_notification.evaluation_notifications.find_users_by_department")
    @patch("app.services.ecn_notification.evaluation_notifications.find_department_manager")
    def test_no_evaluator_no_dept_users_early_return(self, mock_mgr, mock_dept, mock_dispatcher):
        db = MagicMock()
        mock_dept.return_value = []
        ecn = _make_ecn()
        ev = _make_evaluation()
        # Should return early without calling dispatcher
        notify_evaluation_assigned(db, ecn, ev, evaluator_id=None)
        mock_dispatcher.assert_not_called()

    @patch("app.services.ecn_notification.evaluation_notifications.NotificationDispatcher")
    @patch("app.services.ecn_notification.evaluation_notifications.find_users_by_department")
    @patch("app.services.ecn_notification.evaluation_notifications.find_department_manager")
    def test_evaluator_not_in_db_early_return(self, mock_mgr, mock_dept, mock_dispatcher):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        ecn = _make_ecn()
        ev = _make_evaluation()
        notify_evaluation_assigned(db, ecn, ev, evaluator_id=999)
        mock_dispatcher.assert_not_called()


class TestNotifyEvaluationCompleted:
    @patch("app.services.ecn_notification.evaluation_notifications.check_all_evaluations_completed")
    @patch("app.services.ecn_notification.evaluation_notifications.NotificationDispatcher")
    def test_notifies_applicant(self, mock_dispatcher, mock_check):
        db = MagicMock()
        mock_check.return_value = False
        dispatcher_instance = MagicMock()
        mock_dispatcher.return_value = dispatcher_instance

        ecn = _make_ecn(applicant_id=10, project_id=None)
        ev = _make_evaluation()
        notify_evaluation_completed(db, ecn, ev)

        dispatcher_instance.send_notification_request.assert_called()

    @patch("app.services.ecn_notification.evaluation_notifications.check_all_evaluations_completed")
    @patch("app.services.ecn_notification.evaluation_notifications.NotificationDispatcher")
    def test_notifies_project_members_when_project_exists(self, mock_dispatcher, mock_check):
        db = MagicMock()
        mock_check.return_value = False
        dispatcher_instance = MagicMock()
        mock_dispatcher.return_value = dispatcher_instance

        member = MagicMock()
        member.user_id = 20
        db.query.return_value.filter.return_value.all.return_value = [member]

        ecn = _make_ecn(applicant_id=10, project_id=5)
        ev = _make_evaluation()
        notify_evaluation_completed(db, ecn, ev)
        # dispatcher should be called multiple times (applicant + member)
        assert dispatcher_instance.send_notification_request.call_count >= 1
