# -*- coding: utf-8 -*-
"""第十八批 - ECN状态处理器单元测试"""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

try:
    from app.services.status_handlers.ecn_handler import ECNStatusHandler
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def handler(db):
    return ECNStatusHandler(db)


def make_project(project_id=1, health="H1", planned_end=None, description=""):
    p = MagicMock()
    p.id = project_id
    p.health = health
    p.planned_end_date = planned_end or date(2024, 12, 31)
    p.description = description
    p.stage = "S3"
    p.status = "ST01"
    return p


def make_ecn(ecn_id=1, ecn_no="ECN-001"):
    e = MagicMock()
    e.id = ecn_id
    e.ecn_no = ecn_no
    return e


class TestECNStatusHandlerInit:
    def test_db_set(self, db, handler):
        assert handler.db is db

    def test_parent_defaults_none(self, db):
        h = ECNStatusHandler(db)
        assert h._parent is None


class TestHandleEcnScheduleImpact:
    def test_returns_false_if_project_not_found(self, db, handler):
        db.query.return_value.filter.return_value.first.return_value = None
        result = handler.handle_ecn_schedule_impact(999, 1, 5)
        assert result is False

    def test_returns_false_if_ecn_not_found(self, db, handler):
        project = make_project()
        ecn_call = [0]

        def query_side(model):
            ecn_call[0] += 1
            m = MagicMock()
            if ecn_call[0] == 1:
                m.filter.return_value.first.return_value = project
            else:
                m.filter.return_value.first.return_value = None
            return m

        db.query.side_effect = query_side
        result = handler.handle_ecn_schedule_impact(1, 999, 5)
        assert result is False

    def test_updates_planned_end_date(self, db, handler):
        project = make_project(planned_end=date(2024, 12, 31))
        ecn = make_ecn()

        call_idx = [0]
        def query_side(model):
            call_idx[0] += 1
            m = MagicMock()
            if call_idx[0] == 1:
                m.filter.return_value.first.return_value = project
            else:
                m.filter.return_value.first.return_value = ecn
            return m

        db.query.side_effect = query_side
        result = handler.handle_ecn_schedule_impact(1, 1, 10)

        assert result is True
        assert project.planned_end_date == date(2024, 12, 31) + timedelta(days=10)

    def test_updates_health_when_impact_exceeds_threshold(self, db, handler):
        project = make_project(health="H1")
        ecn = make_ecn()

        call_idx = [0]
        def query_side(model):
            call_idx[0] += 1
            m = MagicMock()
            if call_idx[0] == 1:
                m.filter.return_value.first.return_value = project
            else:
                m.filter.return_value.first.return_value = ecn
            return m

        db.query.side_effect = query_side
        handler.handle_ecn_schedule_impact(1, 1, 8)

        assert project.health == "H2"

    def test_no_health_change_when_impact_small(self, db, handler):
        project = make_project(health="H1")
        ecn = make_ecn()

        call_idx = [0]
        def query_side(model):
            call_idx[0] += 1
            m = MagicMock()
            if call_idx[0] == 1:
                m.filter.return_value.first.return_value = project
            else:
                m.filter.return_value.first.return_value = ecn
            return m

        db.query.side_effect = query_side
        handler.handle_ecn_schedule_impact(1, 1, 3)

        assert project.health == "H1"

    def test_commits_on_success(self, db, handler):
        project = make_project()
        ecn = make_ecn()

        call_idx = [0]
        def query_side(model):
            call_idx[0] += 1
            m = MagicMock()
            if call_idx[0] == 1:
                m.filter.return_value.first.return_value = project
            else:
                m.filter.return_value.first.return_value = ecn
            return m

        db.query.side_effect = query_side
        handler.handle_ecn_schedule_impact(1, 1, 5)
        db.commit.assert_called_once()
