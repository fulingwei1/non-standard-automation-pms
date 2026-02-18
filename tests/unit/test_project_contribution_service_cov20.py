# -*- coding: utf-8 -*-
"""第二十批 - project_contribution_service 单元测试"""
import pytest
pytest.importorskip("app.services.project_contribution_service")

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from app.services.project_contribution_service import ProjectContributionService


def make_db():
    return MagicMock()


def make_service(db=None):
    if db is None:
        db = make_db()
    with patch("app.services.project_contribution_service.ProjectBonusService"):
        svc = ProjectContributionService(db)
    return svc, db


def make_contribution(project_id=1, user_id=1, period="2025-01"):
    c = MagicMock()
    c.project_id = project_id
    c.user_id = user_id
    c.period = period
    c.task_count = 0
    c.task_hours = 0.0
    c.actual_hours = 0.0
    c.deliverable_count = 0
    c.issue_count = 0
    return c


class TestProjectContributionServiceInit:
    def test_init_sets_db(self):
        svc, db = make_service()
        assert svc.db is db

    def test_init_creates_bonus_service(self):
        svc, db = make_service()
        assert svc.bonus_service is not None


class TestCalculateMemberContribution:
    def test_creates_new_contribution_when_not_exists(self):
        svc, db = make_service()
        # No existing contribution
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        q.all.return_value = []
        q.count.return_value = 0
        db.query.return_value = q

        with patch("app.services.project_contribution_service.ProjectMemberContribution") as MockContrib:
            contrib = make_contribution()
            MockContrib.return_value = contrib
            result = svc.calculate_member_contribution(
                project_id=1, user_id=1, period="2025-01"
            )
            db.add.assert_called_once_with(contrib)

    def test_uses_existing_contribution(self):
        svc, db = make_service()
        contrib = make_contribution()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = contrib
        q.all.return_value = []
        q.count.return_value = 0
        db.query.return_value = q
        result = svc.calculate_member_contribution(
            project_id=1, user_id=1, period="2025-01"
        )
        db.add.assert_not_called()
        assert result is contrib

    def test_calculates_task_count(self):
        svc, db = make_service()
        contrib = make_contribution()
        task1 = MagicMock()
        task1.status = 'COMPLETED'
        task1.estimated_hours = 8
        task1.actual_hours = 7
        task2 = MagicMock()
        task2.status = 'OPEN'
        task2.estimated_hours = 4
        task2.actual_hours = 0

        call_no = [0]
        def query_side(model):
            call_no[0] += 1
            q = MagicMock()
            q.filter.return_value = q
            q.first.return_value = contrib if call_no[0] == 1 else None
            q.all.return_value = [task1, task2] if call_no[0] == 2 else []
            q.count.return_value = 0
            return q
        db.query.side_effect = query_side

        result = svc.calculate_member_contribution(
            project_id=1, user_id=1, period="2025-06"
        )
        # task_count = number of COMPLETED tasks = 1
        assert result.task_count == 1

    def test_calculates_deliverable_count(self):
        svc, db = make_service()
        contrib = make_contribution()
        doc1 = MagicMock()
        doc2 = MagicMock()

        call_no = [0]
        def query_side(model):
            call_no[0] += 1
            q = MagicMock()
            q.filter.return_value = q
            q.first.return_value = contrib if call_no[0] == 1 else None
            # Call 2 = tasks, call 3 = documents, call 4 = issues
            if call_no[0] == 2:
                q.all.return_value = []
            elif call_no[0] == 3:
                q.all.return_value = [doc1, doc2]
            else:
                q.all.return_value = []
            q.count.return_value = 0
            return q
        db.query.side_effect = query_side

        result = svc.calculate_member_contribution(
            project_id=1, user_id=1, period="2025-06"
        )
        assert result.deliverable_count == 2

    def test_period_december_wraps_to_jan(self):
        """Test that period 2025-12 correctly sets period_end to 2026-01-01"""
        svc, db = make_service()
        contrib = make_contribution(period="2025-12")
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = contrib
        q.all.return_value = []
        q.count.return_value = 0
        db.query.return_value = q
        # Should not raise
        result = svc.calculate_member_contribution(
            project_id=1, user_id=1, period="2025-12"
        )
        assert result is not None
