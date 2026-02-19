# -*- coding: utf-8 -*-
"""第四十六批 - 年度重点工作进度管理单元测试"""
import pytest
from decimal import Decimal

pytest.importorskip("app.services.strategy.annual_work_service.progress",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock, patch
from app.services.strategy.annual_work_service.progress import (
    update_progress,
    calculate_progress_from_projects,
    sync_progress_from_projects,
)


def _make_db():
    return MagicMock()


def _make_work(work_id=1):
    w = MagicMock()
    w.id = work_id
    w.is_active = True
    w.progress_percent = Decimal("0")
    w.status = "NOT_STARTED"
    return w


class TestUpdateProgress:
    def test_returns_none_when_work_not_found(self):
        db = _make_db()
        with patch("app.services.strategy.annual_work_service.progress.get_annual_work",
                   return_value=None):
            result = update_progress(db, 99, MagicMock())
        assert result is None

    def test_sets_completed_when_100(self):
        db = _make_db()
        work = _make_work()
        data = MagicMock()
        data.progress_percent = 100
        data.progress_description = "完成了"
        with patch("app.services.strategy.annual_work_service.progress.get_annual_work",
                   return_value=work):
            update_progress(db, 1, data)
        assert work.status == "COMPLETED"
        db.commit.assert_called_once()

    def test_sets_in_progress_when_partial(self):
        db = _make_db()
        work = _make_work()
        data = MagicMock()
        data.progress_percent = 50
        data.progress_description = None
        with patch("app.services.strategy.annual_work_service.progress.get_annual_work",
                   return_value=work):
            update_progress(db, 1, data)
        assert work.status == "IN_PROGRESS"

    def test_no_status_change_when_zero(self):
        db = _make_db()
        work = _make_work()
        work.status = "NOT_STARTED"
        data = MagicMock()
        data.progress_percent = 0
        data.progress_description = None
        with patch("app.services.strategy.annual_work_service.progress.get_annual_work",
                   return_value=work):
            update_progress(db, 1, data)
        assert work.status == "NOT_STARTED"


class TestCalculateProgressFromProjects:
    def test_returns_none_when_no_links(self):
        db = _make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        result = calculate_progress_from_projects(db, 1)
        assert result is None

    def test_calculates_weighted_progress(self):
        db = _make_db()
        link = MagicMock()
        link.project_id = 10
        link.contribution_weight = Decimal("1")

        from app.models.project import Project as _Project
        project_mock = MagicMock()
        project_mock.progress = 80

        def query_side(model):
            q = MagicMock()
            if model.__name__ if hasattr(model, '__name__') else str(model) == "AnnualKeyWorkProjectLink":
                q.filter.return_value.all.return_value = [link]
            else:
                q.filter.return_value.first.return_value = project_mock
            return q

        db.query.side_effect = None
        db.query.return_value.filter.return_value.all.return_value = [link]

        with patch("app.services.strategy.annual_work_service.progress.db") if False else patch(
            "app.models.project.Project", create=True
        ):
            # 简化：直接patch db.query路径
            call_count = [0]

            def query_dispatch(model):
                call_count[0] += 1
                q = MagicMock()
                if call_count[0] == 1:
                    q.filter.return_value.all.return_value = [link]
                else:
                    q.filter.return_value.first.return_value = project_mock
                return q

            db.query.side_effect = query_dispatch
            result = calculate_progress_from_projects(db, 1)

        assert result == Decimal("80")


class TestSyncProgressFromProjects:
    def test_returns_none_when_no_progress(self):
        db = _make_db()
        with patch("app.services.strategy.annual_work_service.progress.calculate_progress_from_projects",
                   return_value=None):
            result = sync_progress_from_projects(db, 1)
        assert result is None

    def test_syncs_and_returns_work(self):
        db = _make_db()
        work = _make_work()
        with patch("app.services.strategy.annual_work_service.progress.calculate_progress_from_projects",
                   return_value=Decimal("75")), \
             patch("app.services.strategy.annual_work_service.progress.get_annual_work",
                   return_value=work):
            result = sync_progress_from_projects(db, 1)
        assert work.progress_percent == Decimal("75")
        assert work.status == "IN_PROGRESS"
        db.commit.assert_called_once()
