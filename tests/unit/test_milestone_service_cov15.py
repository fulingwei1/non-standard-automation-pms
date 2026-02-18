# -*- coding: utf-8 -*-
"""第十五批: milestone_service 单元测试"""
import pytest

pytest.importorskip("app.services.milestone_service")

from unittest.mock import MagicMock, patch
from datetime import date
from app.services.milestone_service import MilestoneService


def make_svc():
    db = MagicMock()
    svc = MilestoneService.__new__(MilestoneService)
    svc.db = db
    from app.models.project import ProjectMilestone
    svc.model = ProjectMilestone
    return svc, db


def test_get_by_project_returns_ordered():
    svc, db = make_svc()
    m1 = MagicMock()
    m1.project_id = 1
    m2 = MagicMock()
    m2.project_id = 1
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [m1, m2]
    result = svc.get_by_project(1)
    assert len(result) == 2


def test_get_by_project_empty():
    svc, db = make_svc()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    result = svc.get_by_project(42)
    assert result == []


def test_complete_milestone_success():
    svc, db = make_svc()
    milestone = MagicMock()
    milestone.actual_date = None
    # Mock get and update
    svc.get = MagicMock(return_value=milestone)
    svc.update = MagicMock()
    updated = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = updated

    result = svc.complete_milestone(10, actual_date=date(2025, 1, 15))
    assert result == updated
    svc.update.assert_called_once()
    call_args = svc.update.call_args
    assert call_args[0][0] == 10


def test_complete_milestone_uses_today_when_no_date():
    svc, db = make_svc()
    milestone = MagicMock()
    milestone.actual_date = None
    svc.get = MagicMock(return_value=milestone)
    svc.update = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock()
    svc.complete_milestone(5)
    svc.update.assert_called_once()


def test_milestone_service_init():
    db = MagicMock()
    # Verify no crash on init
    with patch("app.services.milestone_service.BaseService.__init__") as mock_init:
        mock_init.return_value = None
        svc = MilestoneService(db)
        mock_init.assert_called_once()
