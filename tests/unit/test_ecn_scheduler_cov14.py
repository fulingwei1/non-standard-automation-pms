# -*- coding: utf-8 -*-
"""
第十四批：ECN定时任务服务 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

try:
    from app.services import ecn_scheduler
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_ecn(**kwargs):
    ecn = MagicMock()
    ecn.id = kwargs.get("id", 1)
    ecn.ecn_no = kwargs.get("ecn_no", "ECN-2025-001")
    ecn.ecn_title = "变更标题"
    return ecn


class TestEcnScheduler:
    def test_check_evaluation_overdue_no_overdue(self):
        db = make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        alerts = ecn_scheduler.check_evaluation_overdue(db)
        assert alerts == []

    def test_check_evaluation_overdue_with_overdue(self):
        db = make_db()
        eval_mock = MagicMock()
        eval_mock.ecn_id = 1
        eval_mock.id = 10
        eval_mock.eval_dept = "工程部"
        eval_mock.created_at = datetime.now() - timedelta(days=5)
        ecn = make_ecn()
        # first query: evaluations, second query: ecn
        db.query.return_value.filter.return_value.all.return_value = [eval_mock]
        db.query.return_value.filter.return_value.first.return_value = ecn
        alerts = ecn_scheduler.check_evaluation_overdue(db)
        assert len(alerts) == 1
        assert alerts[0]["type"] == "EVALUATION_OVERDUE"
        assert alerts[0]["ecn_no"] == "ECN-2025-001"

    def test_check_approval_overdue_no_overdue(self):
        db = make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        alerts = ecn_scheduler.check_approval_overdue(db)
        assert alerts == []

    def test_check_approval_overdue_with_overdue(self):
        db = make_db()
        approval = MagicMock()
        approval.ecn_id = 1
        approval.id = 20
        approval.approval_level = 1
        approval.approval_role = "总监"
        approval.due_date = datetime.now() - timedelta(days=2)
        approval.is_overdue = False
        ecn = make_ecn()
        db.query.return_value.filter.return_value.all.return_value = [approval]
        db.query.return_value.filter.return_value.first.return_value = ecn
        alerts = ecn_scheduler.check_approval_overdue(db)
        assert len(alerts) == 1
        assert alerts[0]["type"] == "APPROVAL_OVERDUE"
        assert approval.is_overdue is True

    def test_check_task_overdue_no_overdue(self):
        db = make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        alerts = ecn_scheduler.check_task_overdue(db)
        assert alerts == []

    def test_check_task_overdue_with_overdue(self):
        db = make_db()
        from datetime import date
        task = MagicMock()
        task.ecn_id = 1
        task.id = 30
        task.task_name = "修改图纸"
        task.planned_end = date.today() - timedelta(days=3)
        ecn = make_ecn()
        db.query.return_value.filter.return_value.all.return_value = [task]
        db.query.return_value.filter.return_value.first.return_value = ecn
        alerts = ecn_scheduler.check_task_overdue(db)
        assert len(alerts) == 1
        assert alerts[0]["type"] == "TASK_OVERDUE"

    def test_run_ecn_scheduler_no_alerts(self):
        with patch.object(ecn_scheduler, "check_all_overdue", return_value=[]):
            with patch.object(ecn_scheduler, "send_overdue_notifications") as mock_send:
                ecn_scheduler.run_ecn_scheduler()
                mock_send.assert_not_called()

    def test_run_ecn_scheduler_with_alerts(self):
        alerts = [{"type": "TASK_OVERDUE", "ecn_no": "ECN-001"}]
        with patch.object(ecn_scheduler, "check_all_overdue", return_value=alerts):
            with patch.object(ecn_scheduler, "send_overdue_notifications") as mock_send:
                ecn_scheduler.run_ecn_scheduler()
                mock_send.assert_called_once_with(alerts)
