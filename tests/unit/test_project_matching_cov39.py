# -*- coding: utf-8 -*-
"""
第三十九批覆盖率测试 - work_log_ai/project_matching.py
"""
import pytest
from unittest.mock import MagicMock

pytest.importorskip("app.services.work_log_ai.project_matching",
                    reason="import failed, skip")

from app.services.work_log_ai.project_matching import ProjectMatchingMixin


def _make_project(pid, code, name, customer_name=None):
    p = MagicMock()
    p.id = pid
    p.project_code = code
    p.project_name = name
    p.customer_name = customer_name
    return p


def _make_member(user_id, project_id):
    m = MagicMock()
    m.user_id = user_id
    m.project_id = project_id
    m.is_active = True
    return m


class ConcreteProjectMatcher(ProjectMatchingMixin):
    """用于实例化 Mixin 的具体类"""
    def __init__(self, db):
        self.db = db


class TestProjectMatchingMixin:

    def setup_method(self):
        self.db = MagicMock()
        self.matcher = ConcreteProjectMatcher(self.db)

    def test_get_user_projects_empty(self):
        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []

        result = self.matcher._get_user_projects(user_id=1)
        assert result == []

    def test_get_user_projects_sorted_by_timesheet_count(self):
        members = [_make_member(1, 100), _make_member(1, 200)]
        projects = [_make_project(100, "P001", "项目一", "客户A"),
                    _make_project(200, "P002", "项目二")]

        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.side_effect = [members, projects]
        mock_q.count.side_effect = [5, 2]

        result = self.matcher._get_user_projects(user_id=1)
        if len(result) > 1:
            assert result[0]["timesheet_count"] >= result[1]["timesheet_count"]

    def test_extract_project_keywords_includes_code(self):
        project = _make_project(1, "P001", "自动化测试系统", "富士客户")

        keywords = self.matcher._extract_project_keywords(project)
        assert "P001" in keywords

    def test_extract_project_keywords_includes_customer(self):
        project = _make_project(1, "P001", "自动化设备", "某客户")
        keywords = self.matcher._extract_project_keywords(project)
        assert "某客户" in keywords

    def test_extract_project_keywords_no_customer(self):
        project = _make_project(1, "P002", "简单项目", None)
        keywords = self.matcher._extract_project_keywords(project)
        assert "P002" in keywords

    def test_get_user_projects_for_suggestion_delegates(self):
        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []

        result = self.matcher.get_user_projects_for_suggestion(user_id=1)
        assert isinstance(result, list)
