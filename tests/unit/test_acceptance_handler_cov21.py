# -*- coding: utf-8 -*-
"""第二十一批：验收状态处理器单元测试"""

import pytest
from unittest.mock import MagicMock, call
from datetime import datetime

pytest.importorskip("app.services.status_handlers.acceptance_handler")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def handler(mock_db):
    from app.services.status_handlers.acceptance_handler import AcceptanceStatusHandler
    return AcceptanceStatusHandler(mock_db)


def _make_project(stage="S7", status="ST20", health="H2"):
    p = MagicMock()
    p.id = 1
    p.stage = stage
    p.status = status
    p.health = health
    p.description = None
    return p


class TestHandleFatPassed:
    def test_project_not_found_returns_false(self, handler, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = handler.handle_fat_passed(project_id=99)
        assert result is False

    def test_wrong_stage_returns_false(self, handler, mock_db):
        project = _make_project(stage="S8")
        mock_db.query.return_value.filter.return_value.first.return_value = project
        result = handler.handle_fat_passed(project_id=1)
        assert result is False

    def test_fat_passed_updates_stage(self, handler, mock_db):
        project = _make_project(stage="S7", health="H2")
        mock_db.query.return_value.filter.return_value.first.return_value = project
        result = handler.handle_fat_passed(project_id=1)
        assert result is True
        assert project.stage == "S8"
        assert project.status == "ST23"
        assert project.health == "H1"
        mock_db.commit.assert_called_once()


class TestHandleFatFailed:
    def test_project_not_found_returns_false(self, handler, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = handler.handle_fat_failed(project_id=99)
        assert result is False

    def test_fat_failed_updates_health_and_status(self, handler, mock_db):
        project = _make_project(stage="S7", status="ST21", health="H1")
        mock_db.query.return_value.filter.return_value.first.return_value = project
        result = handler.handle_fat_failed(project_id=1, issues=["缺少防尘罩", "电气接线错误"])
        assert result is True
        assert project.status == "ST22"
        assert project.health == "H2"
        assert "缺少防尘罩" in (project.description or "")
        mock_db.commit.assert_called_once()


class TestHandleSatPassed:
    def test_wrong_stage_returns_false(self, handler, mock_db):
        project = _make_project(stage="S7")
        mock_db.query.return_value.filter.return_value.first.return_value = project
        result = handler.handle_sat_passed(project_id=1)
        assert result is False

    def test_sat_passed_updates_status(self, handler, mock_db):
        project = _make_project(stage="S8", status="ST24")
        mock_db.query.return_value.filter.return_value.first.return_value = project
        result = handler.handle_sat_passed(project_id=1)
        assert result is True
        assert project.status == "ST27"
        mock_db.commit.assert_called_once()


class TestHandleSatFailed:
    def test_sat_failed_appends_issues(self, handler, mock_db):
        project = _make_project(stage="S8", status="ST25", health="H1")
        project.description = "原有描述"
        mock_db.query.return_value.filter.return_value.first.return_value = project
        result = handler.handle_sat_failed(project_id=1, issues=["SAT问题1"])
        assert result is True
        assert project.status == "ST26"
        assert project.health == "H2"
        assert "SAT验收不通过" in project.description


class TestHandleFinalAcceptancePassed:
    def test_project_in_s8_returns_true(self, handler, mock_db):
        project = _make_project(stage="S8")
        mock_db.query.return_value.filter.return_value.first.return_value = project
        result = handler.handle_final_acceptance_passed(project_id=1)
        assert result is True

    def test_project_not_in_s8_returns_false(self, handler, mock_db):
        project = _make_project(stage="S7")
        mock_db.query.return_value.filter.return_value.first.return_value = project
        result = handler.handle_final_acceptance_passed(project_id=1)
        assert result is False
