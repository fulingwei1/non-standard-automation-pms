# -*- coding: utf-8 -*-
"""Tests for ecn_scheduler.py"""
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from app.services.ecn_scheduler import (
    check_evaluation_overdue,
    check_approval_overdue,
    check_task_overdue,
)


class TestCheckEvaluationOverdue:
    def test_no_overdue(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = check_evaluation_overdue(db)
        assert result == []

    def test_overdue_found(self):
        db = MagicMock()
        eval_obj = MagicMock(id=1, ecn_id=1, eval_dept="质量部",
                             created_at=datetime.now() - timedelta(days=5))
        ecn = MagicMock(id=1, ecn_no="ECN-001", ecn_title="变更1")
        db.query.return_value.filter.return_value.all.return_value = [eval_obj]
        db.query.return_value.filter.return_value.first.return_value = ecn
        result = check_evaluation_overdue(db)
        assert len(result) == 1
        assert result[0]['type'] == 'EVALUATION_OVERDUE'
        assert result[0]['overdue_days'] >= 5

    def test_no_ecn(self):
        db = MagicMock()
        eval_obj = MagicMock(id=1, ecn_id=1, eval_dept="质量部",
                             created_at=datetime.now() - timedelta(days=5))
        db.query.return_value.filter.return_value.all.return_value = [eval_obj]
        db.query.return_value.filter.return_value.first.return_value = None
        result = check_evaluation_overdue(db)
        assert result == []


class TestCheckApprovalOverdue:
    def test_overdue_found(self):
        db = MagicMock()
        approval = MagicMock(id=1, ecn_id=1, status="PENDING",
                             due_date=datetime.now() - timedelta(days=2),
                             approval_level=1, approval_role="技术总监")
        ecn = MagicMock(id=1, ecn_no="ECN-001", ecn_title="变更1")
        db.query.return_value.filter.return_value.all.return_value = [approval]
        db.query.return_value.filter.return_value.first.return_value = ecn
        result = check_approval_overdue(db)
        assert len(result) == 1
        assert result[0]['type'] == 'APPROVAL_OVERDUE'
        db.commit.assert_called_once()

    def test_no_overdue(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = check_approval_overdue(db)
        assert result == []


class TestCheckTaskOverdue:
    def test_overdue_found(self):
        db = MagicMock()
        task = MagicMock(id=1, ecn_id=1, task_name="更新BOM",
                         planned_end=datetime.now().date() - timedelta(days=3))
        ecn = MagicMock(id=1, ecn_no="ECN-001", ecn_title="变更1")
        db.query.return_value.filter.return_value.all.return_value = [task]
        db.query.return_value.filter.return_value.first.return_value = ecn
        result = check_task_overdue(db)
        assert len(result) == 1
        assert result[0]['type'] == 'TASK_OVERDUE'

    def test_no_overdue(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = check_task_overdue(db)
        assert result == []
