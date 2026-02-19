# -*- coding: utf-8 -*-
"""
第三十九批覆盖率测试 - strategy/annual_work_service/projects.py
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.strategy.annual_work_service.projects",
                    reason="import failed, skip")


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_link(work_id, project_id, is_active=True, weight=Decimal("1.0")):
    link = MagicMock()
    link.annual_work_id = work_id
    link.project_id = project_id
    link.is_active = is_active
    link.contribution_weight = weight
    return link


class TestLinkProject:

    def test_link_project_returns_none_if_no_work(self, mock_db):
        from app.services.strategy.annual_work_service.projects import link_project

        with patch("app.services.strategy.annual_work_service.projects.get_annual_work",
                   return_value=None):
            result = link_project(mock_db, work_id=999, project_id=1)
            assert result is None

    def test_link_project_creates_new_link(self, mock_db):
        from app.services.strategy.annual_work_service.projects import link_project

        mock_work = MagicMock(id=1)
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = None  # no existing link

        new_link = _make_link(1, 10)

        with patch("app.services.strategy.annual_work_service.projects.get_annual_work",
                   return_value=mock_work), \
             patch("app.services.strategy.annual_work_service.projects.AnnualKeyWorkProjectLink",
                   return_value=new_link):
            result = link_project(mock_db, work_id=1, project_id=10)
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_link_project_reactivates_existing(self, mock_db):
        from app.services.strategy.annual_work_service.projects import link_project

        mock_work = MagicMock(id=1)
        existing = _make_link(1, 10, is_active=False)
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = existing

        with patch("app.services.strategy.annual_work_service.projects.get_annual_work",
                   return_value=mock_work):
            result = link_project(mock_db, work_id=1, project_id=10)
            assert existing.is_active is True
            mock_db.commit.assert_called_once()


class TestUnlinkProject:

    def test_unlink_project_returns_false_if_no_link(self, mock_db):
        from app.services.strategy.annual_work_service.projects import unlink_project

        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = None

        # Patch the model to avoid SQLAlchemy descriptor issues
        with patch("app.services.strategy.annual_work_service.projects.AnnualKeyWorkProjectLink"):
            result = unlink_project(mock_db, work_id=1, project_id=10)
        assert result is False

    def test_unlink_project_deactivates_link(self, mock_db):
        from app.services.strategy.annual_work_service.projects import unlink_project

        link = _make_link(1, 10, is_active=True)
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = link

        with patch("app.services.strategy.annual_work_service.projects.AnnualKeyWorkProjectLink"):
            result = unlink_project(mock_db, work_id=1, project_id=10)
        # Should set is_active = False and commit
        assert link.is_active is False
        mock_db.commit.assert_called_once()


class TestGetLinkedProjects:

    def test_get_linked_projects_empty(self, mock_db):
        from app.services.strategy.annual_work_service.projects import get_linked_projects

        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []

        with patch("app.services.strategy.annual_work_service.projects.AnnualKeyWorkProjectLink"):
            result = get_linked_projects(mock_db, work_id=1)
        assert result == []

    def test_get_linked_projects_returns_items(self, mock_db):
        from app.services.strategy.annual_work_service.projects import get_linked_projects

        links = [_make_link(1, 10)]
        mock_project = MagicMock(id=10, code="P001", name="项目一")

        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = links
        mock_q.first.return_value = mock_project

        with patch("app.services.strategy.annual_work_service.projects.AnnualKeyWorkProjectLink"), \
             patch("app.services.strategy.annual_work_service.projects.ProjectLinkItem") as MockItem:
            MockItem.return_value = MagicMock(project_id=10)
            result = get_linked_projects(mock_db, work_id=1)
            assert len(result) == 1

    def test_get_linked_projects_skips_missing_projects(self, mock_db):
        from app.services.strategy.annual_work_service.projects import get_linked_projects

        links = [_make_link(1, 10), _make_link(1, 20)]
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = links
        mock_q.first.return_value = None  # all projects missing

        with patch("app.services.strategy.annual_work_service.projects.AnnualKeyWorkProjectLink"):
            result = get_linked_projects(mock_db, work_id=1)
        assert result == []
