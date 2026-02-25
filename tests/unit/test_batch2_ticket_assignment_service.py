# -*- coding: utf-8 -*-
"""Ticket Assignment Service 测试 - Batch 2"""
from unittest.mock import MagicMock, patch
import pytest

from app.services.ticket_assignment_service import (
    get_project_members_for_ticket, get_ticket_related_projects
)


@pytest.fixture
def mock_db():
    return MagicMock()


def make_member(user_id, username, real_name, role_code, project_id, is_lead=False, is_active=True):
    m = MagicMock()
    m.user_id = user_id
    m.is_active = is_active
    m.role_code = role_code
    m.is_lead = is_lead
    m.project_id = project_id
    m.allocation_pct = 100

    user = MagicMock()
    user.username = username
    user.real_name = real_name
    user.email = f"{username}@test.com"
    user.phone = "123"
    user.department = "研发部"
    user.position = "工程师"
    m.user = user

    role_type = MagicMock()
    role_type.role_name = role_code
    m.role_type = role_type

    project = MagicMock()
    project.project_code = f"P{project_id:03d}"
    project.project_name = f"Project {project_id}"
    m.project = project

    return m


class TestGetProjectMembersForTicket:
    def test_empty_project_ids(self, mock_db):
        result = get_project_members_for_ticket(mock_db, [])
        assert result == []

    def test_no_members_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = get_project_members_for_ticket(mock_db, [1])
        assert result == []

    def test_single_member(self, mock_db):
        member = make_member(1, "zhangsan", "张三", "PM", 1, is_lead=True)
        mock_db.query.return_value.filter.return_value.all.return_value = [member]
        result = get_project_members_for_ticket(mock_db, [1])
        assert len(result) == 1
        assert result[0]["user_id"] == 1
        assert result[0]["real_name"] == "张三"
        assert result[0]["is_lead"] is True

    def test_dedup_across_projects(self, mock_db):
        m1 = make_member(1, "zhangsan", "张三", "PM", 1)
        m2 = make_member(1, "zhangsan", "张三", "PM", 2)
        mock_db.query.return_value.filter.return_value.all.return_value = [m1, m2]
        result = get_project_members_for_ticket(mock_db, [1, 2])
        assert len(result) == 1
        assert len(result[0]["projects"]) == 2

    def test_include_roles_filter(self, mock_db):
        m1 = make_member(1, "a", "A", "PM", 1)
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [m1]
        result = get_project_members_for_ticket(mock_db, [1], include_roles=["PM"])
        assert len(result) == 1

    def test_exclude_user_id(self, mock_db):
        m1 = make_member(1, "a", "A", "PM", 1)
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [m1]
        result = get_project_members_for_ticket(mock_db, [1], exclude_user_id=2)
        assert len(result) == 1

    def test_sorted_by_role_priority(self, mock_db):
        m1 = make_member(1, "qa", "QA人员", "QA", 1)
        m2 = make_member(2, "pm", "项目经理", "PM", 1)
        mock_db.query.return_value.filter.return_value.all.return_value = [m1, m2]
        result = get_project_members_for_ticket(mock_db, [1])
        assert result[0]["role_code"] == "PM"
        assert result[1]["role_code"] == "QA"

    def test_unknown_role_priority(self, mock_db):
        m1 = make_member(1, "a", "A", "UNKNOWN_ROLE", 1)
        mock_db.query.return_value.filter.return_value.all.return_value = [m1]
        result = get_project_members_for_ticket(mock_db, [1])
        assert len(result) == 1

    def test_no_role_type(self, mock_db):
        m = make_member(1, "a", "A", "PM", 1)
        m.role_type = None
        mock_db.query.return_value.filter.return_value.all.return_value = [m]
        result = get_project_members_for_ticket(mock_db, [1])
        assert result[0]["role_name"] == "PM"

    def test_no_user(self, mock_db):
        m = make_member(1, "a", "A", "PM", 1)
        m.user = None
        mock_db.query.return_value.filter.return_value.all.return_value = [m]
        result = get_project_members_for_ticket(mock_db, [1])
        assert result[0]["username"] == "Unknown"

    def test_include_roles_and_exclude_combined(self, mock_db):
        m1 = make_member(1, "a", "A", "PM", 1)
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [m1]
        result = get_project_members_for_ticket(mock_db, [1], include_roles=["PM"], exclude_user_id=99)
        assert len(result) == 1


class TestGetTicketRelatedProjects:
    def test_ticket_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = get_ticket_related_projects(mock_db, 999)
        assert result["primary_project"] is None
        assert result["related_projects"] == []

    def test_ticket_with_primary_project(self, mock_db):
        ticket = MagicMock()
        ticket.id = 1
        ticket.project_id = 10

        project = MagicMock()
        project.id = 10
        project.project_code = "P010"
        project.project_name = "Main Project"

        # first query returns ticket, second returns project, third returns empty related
        mock_db.query.return_value.filter.return_value.first.side_effect = [ticket, project]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_ticket_related_projects(mock_db, 1)
        assert result["primary_project"]["id"] == 10

    def test_ticket_no_project(self, mock_db):
        ticket = MagicMock()
        ticket.id = 1
        ticket.project_id = None

        mock_db.query.return_value.filter.return_value.first.return_value = ticket
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_ticket_related_projects(mock_db, 1)
        assert result["primary_project"] is None

    def test_with_related_projects(self, mock_db):
        ticket = MagicMock()
        ticket.id = 1
        ticket.project_id = 10

        project_main = MagicMock()
        project_main.id = 10
        project_main.project_code = "P010"
        project_main.project_name = "Main"

        tp = MagicMock()
        tp.project_id = 20
        tp.is_primary = False

        project_related = MagicMock()
        project_related.id = 20
        project_related.project_code = "P020"
        project_related.project_name = "Related"

        mock_db.query.return_value.filter.return_value.first.side_effect = [ticket, project_main, project_related]
        mock_db.query.return_value.filter.return_value.all.return_value = [tp]

        result = get_ticket_related_projects(mock_db, 1)
        assert len(result["related_projects"]) == 1
