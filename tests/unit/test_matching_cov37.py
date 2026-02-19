# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - 项目匹配模块
tests/unit/test_matching_cov37.py
"""
import pytest
from unittest.mock import MagicMock, call, patch

pytest.importorskip("app.services.work_log_ai.project_matching")

from app.services.work_log_ai.project_matching import ProjectMatchingMixin


class ConcreteMatching(ProjectMatchingMixin):
    """具体化混入以便测试"""
    def __init__(self, db):
        self.db = db


def _make_db(members=None, projects=None, timesheet_count=3):
    db = MagicMock()

    if members is None:
        members = []
    if projects is None:
        projects = []

    # ProjectMember query
    m_query = MagicMock()
    m_query.filter.return_value.all.return_value = members
    # Project query
    p_query = MagicMock()
    p_query.filter.return_value.all.return_value = projects
    # Timesheet count
    t_query = MagicMock()
    t_query.filter.return_value.count.return_value = timesheet_count

    def query_side_effect(model):
        from app.models.project import ProjectMember, Project
        from app.models.timesheet import Timesheet
        if model is ProjectMember:
            return m_query
        elif model is Project:
            return p_query
        elif model is Timesheet:
            return t_query
        return MagicMock()

    db.query.side_effect = query_side_effect
    return db


def _make_member(user_id=1, project_id=10):
    m = MagicMock()
    m.user_id = user_id
    m.project_id = project_id
    m.is_active = True
    return m


def _make_project(pid=10, code="P010", name="测试设备项目", customer="客户A"):
    p = MagicMock()
    p.id = pid
    p.project_code = code
    p.project_name = name
    p.customer_name = customer
    p.is_active = True
    return p


class TestProjectMatchingMixin:
    def test_get_user_projects_returns_list(self):
        member = _make_member()
        project = _make_project()
        db = _make_db(members=[member], projects=[project])
        m = ConcreteMatching(db)
        result = m._get_user_projects(1)
        assert isinstance(result, list)

    def test_get_user_projects_includes_timesheet_count(self):
        member = _make_member()
        project = _make_project()
        db = _make_db(members=[member], projects=[project], timesheet_count=5)
        m = ConcreteMatching(db)
        result = m._get_user_projects(1)
        assert result[0]["timesheet_count"] == 5

    def test_get_user_projects_sorted_by_frequency(self):
        """Projects are sorted descending by timesheet_count"""
        member1 = _make_member(project_id=10)
        member2 = _make_member(project_id=20)
        proj1 = _make_project(pid=10)
        proj2 = _make_project(pid=20)

        db = MagicMock()
        from app.models.project import ProjectMember, Project
        from app.models.timesheet import Timesheet

        call_counts = {"count": 0}

        def query_side(model):
            q = MagicMock()
            if model is ProjectMember:
                q.filter.return_value.all.return_value = [member1, member2]
            elif model is Project:
                q.filter.return_value.all.return_value = [proj1, proj2]
            elif model is Timesheet:
                call_counts["count"] += 1
                cnt = 10 if call_counts["count"] % 2 == 1 else 2
                q.filter.return_value.count.return_value = cnt
            else:
                pass
            return q

        db.query.side_effect = query_side
        m = ConcreteMatching(db)
        result = m._get_user_projects(1)
        if len(result) >= 2:
            assert result[0]["timesheet_count"] >= result[1]["timesheet_count"]

    def test_extract_project_keywords_includes_code(self):
        project = _make_project(code="PROJ-001")
        db = MagicMock()
        m = ConcreteMatching(db)
        keywords = m._extract_project_keywords(project)
        assert "PROJ-001" in keywords

    def test_extract_project_keywords_includes_customer(self):
        project = _make_project(customer="华为技术")
        db = MagicMock()
        m = ConcreteMatching(db)
        keywords = m._extract_project_keywords(project)
        assert "华为技术" in keywords

    def test_get_user_projects_for_suggestion_delegates(self):
        member = _make_member()
        project = _make_project()
        db = _make_db(members=[member], projects=[project])
        m = ConcreteMatching(db)
        result = m.get_user_projects_for_suggestion(1)
        assert isinstance(result, list)

    def test_no_projects_when_no_members(self):
        db = _make_db(members=[], projects=[])
        m = ConcreteMatching(db)
        result = m._get_user_projects(99)
        assert result == []
