# -*- coding: utf-8 -*-
"""
Unit tests for app/services/strategy/annual_work_service/progress.py
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.strategy.annual_work_service.progress import (
        update_progress,
        calculate_progress_from_projects,
        sync_progress_from_projects,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


# ---------------------------------------------------------------------------
# update_progress
# ---------------------------------------------------------------------------

def test_update_progress_returns_none_when_not_found():
    db = MagicMock()
    with patch("app.services.strategy.annual_work_service.progress.get_annual_work", return_value=None):
        data = MagicMock(progress_percent=50, progress_description="desc")
        result = update_progress(db, work_id=999, data=data)
    assert result is None


def test_update_progress_sets_in_progress_status():
    db = MagicMock()
    work_mock = MagicMock()
    with patch("app.services.strategy.annual_work_service.progress.get_annual_work", return_value=work_mock):
        data = MagicMock(progress_percent=Decimal("50"), progress_description="half done")
        update_progress(db, work_id=1, data=data)
    assert work_mock.status == "IN_PROGRESS"


def test_update_progress_sets_completed_status():
    db = MagicMock()
    work_mock = MagicMock()
    with patch("app.services.strategy.annual_work_service.progress.get_annual_work", return_value=work_mock):
        data = MagicMock(progress_percent=Decimal("100"), progress_description="done")
        update_progress(db, work_id=1, data=data)
    assert work_mock.status == "COMPLETED"


def test_update_progress_commits_and_refreshes():
    db = MagicMock()
    work_mock = MagicMock()
    with patch("app.services.strategy.annual_work_service.progress.get_annual_work", return_value=work_mock):
        data = MagicMock(progress_percent=Decimal("80"), progress_description=None)
        update_progress(db, work_id=1, data=data)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(work_mock)


# ---------------------------------------------------------------------------
# calculate_progress_from_projects
# ---------------------------------------------------------------------------

def test_calculate_progress_no_links_returns_none():
    db = MagicMock()
    with patch(
        "app.services.strategy.annual_work_service.progress.AnnualKeyWorkProjectLink"
    ) as MockLink:
        MockLink.annual_work_id = MagicMock()
        MockLink.is_active = MagicMock()
        q = MagicMock()
        q.filter.return_value.all.return_value = []
        db.query.return_value = q
        result = calculate_progress_from_projects(db, work_id=1)
    assert result is None


def test_calculate_progress_weighted_average():
    import sys
    db = MagicMock()

    link1 = MagicMock(project_id=10, contribution_weight=Decimal("1"))
    link2 = MagicMock(project_id=11, contribution_weight=Decimal("1"))

    proj1 = MagicMock(progress=60)
    proj2 = MagicMock(progress=40)

    # Project is imported inside the function body; inject via sys.modules
    mock_proj_module = MagicMock()
    mock_proj_cls = MagicMock()
    mock_proj_module.Project = mock_proj_cls

    with patch(
        "app.services.strategy.annual_work_service.progress.AnnualKeyWorkProjectLink"
    ) as MockLink:
        MockLink.annual_work_id = MagicMock()
        MockLink.is_active = MagicMock()

        link_q = MagicMock()
        link_q.filter.return_value.all.return_value = [link1, link2]

        proj_q = MagicMock()
        proj_q.filter.return_value.first.side_effect = [proj1, proj2]

        db.query.side_effect = [link_q, proj_q, proj_q]

        sys.modules["app.models.project"] = mock_proj_module
        try:
            result = calculate_progress_from_projects(db, work_id=1)
        finally:
            sys.modules.pop("app.models.project", None)

    # (60*1 + 40*1) / 2 = 50
    assert result == Decimal("50")


# ---------------------------------------------------------------------------
# sync_progress_from_projects
# ---------------------------------------------------------------------------

def test_sync_progress_returns_none_when_no_progress():
    db = MagicMock()
    with patch(
        "app.services.strategy.annual_work_service.progress.calculate_progress_from_projects",
        return_value=None,
    ):
        result = sync_progress_from_projects(db, work_id=1)
    assert result is None


def test_sync_progress_updates_work():
    db = MagicMock()
    work_mock = MagicMock()
    with patch(
        "app.services.strategy.annual_work_service.progress.calculate_progress_from_projects",
        return_value=Decimal("75"),
    ), patch(
        "app.services.strategy.annual_work_service.progress.get_annual_work",
        return_value=work_mock,
    ):
        result = sync_progress_from_projects(db, work_id=1)
    assert work_mock.progress_percent == Decimal("75")
    assert work_mock.status == "IN_PROGRESS"
    db.commit.assert_called_once()
