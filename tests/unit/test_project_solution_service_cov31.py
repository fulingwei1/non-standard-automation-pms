# -*- coding: utf-8 -*-
"""
Unit tests for ProjectSolutionService (第三十一批)
"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.project_solution_service import ProjectSolutionService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return ProjectSolutionService(db=mock_db)


def _make_issue(
    issue_id=1,
    title="测试问题",
    issue_type="BUG",
    category="质量",
    severity="HIGH",
    solution="重新设计模块",
    status="RESOLVED",
    resolved_at=None,
    resolved_by_name="张三",
    tags=["稳定性"],
):
    issue = MagicMock()
    issue.id = issue_id
    issue.issue_no = f"ISS-{issue_id:03d}"
    issue.title = title
    issue.issue_type = issue_type
    issue.category = category
    issue.severity = severity
    issue.solution = solution
    issue.status = status
    issue.resolved_at = resolved_at
    issue.resolved_by_name = resolved_by_name
    issue.tags = tags
    return issue


# ---------------------------------------------------------------------------
# get_project_solutions
# ---------------------------------------------------------------------------

class TestGetProjectSolutions:
    def test_returns_solutions_for_project(self, service, mock_db):
        issue = _make_issue()
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.all.return_value = [issue]

        result = service.get_project_solutions(project_id=1)

        assert len(result) == 1
        assert result[0]["issue_id"] == issue.id
        assert result[0]["solution"] == issue.solution

    def test_filters_by_issue_type(self, service, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.all.return_value = []

        result = service.get_project_solutions(project_id=1, issue_type="BUG")
        assert result == []
        # filter 调用应多于 1 次（包含 issue_type 过滤）
        assert chain.filter.call_count >= 2

    def test_returns_empty_when_no_solutions(self, service, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.all.return_value = []

        result = service.get_project_solutions(project_id=99)
        assert result == []

    def test_tags_as_list(self, service, mock_db):
        issue = _make_issue(tags=["tag1", "tag2"])
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.all.return_value = [issue]

        result = service.get_project_solutions(project_id=1)
        assert result[0]["tags"] == ["tag1", "tag2"]

    def test_tags_not_list_returns_empty_list(self, service, mock_db):
        issue = _make_issue(tags="not-a-list")
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.all.return_value = [issue]

        result = service.get_project_solutions(project_id=1)
        assert result[0]["tags"] == []


# ---------------------------------------------------------------------------
# get_solution_templates
# ---------------------------------------------------------------------------

class TestGetSolutionTemplates:
    def test_returns_templates(self, service, mock_db):
        template = MagicMock()
        template.id = 1
        template.name = "标准调试模板"

        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.all.return_value = [template]

        with patch(
            "app.services.project_solution_service.apply_keyword_filter",
            return_value=chain,
        ):
            result = service.get_solution_templates()

        assert result == [template]

    def test_filters_by_issue_type(self, service, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.all.return_value = []

        with patch(
            "app.services.project_solution_service.apply_keyword_filter",
            return_value=chain,
        ):
            result = service.get_solution_templates(issue_type="BUG")

        assert result == []
        assert chain.filter.called
