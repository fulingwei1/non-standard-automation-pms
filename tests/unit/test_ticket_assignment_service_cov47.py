# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - ticket_assignment_service.py
"""
import pytest

pytest.importorskip("app.services.ticket_assignment_service")

from unittest.mock import MagicMock, patch

from app.services.ticket_assignment_service import (
    get_project_members_for_ticket,
    get_ticket_related_projects,
)


def _make_db():
    return MagicMock()


# ---------- get_project_members_for_ticket ----------

def test_get_members_empty_project_ids():
    db = _make_db()
    result = get_project_members_for_ticket(db, project_ids=[])
    assert result == []


def test_get_members_no_members():
    db = _make_db()
    db.query.return_value.filter.return_value.all.return_value = []
    result = get_project_members_for_ticket(db, project_ids=[1, 2])
    assert result == []


def test_get_members_deduplicates():
    """同一用户在多个项目中只出现一次"""
    db = _make_db()

    user = MagicMock()
    user.username = "zhangsan"
    user.real_name = "张三"
    user.email = "z@test.com"
    user.phone = "13800000000"
    user.department = "研发"
    user.position = "工程师"

    member1 = MagicMock()
    member1.user_id = 1
    member1.user = user
    member1.role_code = "ME"
    member1.role_type = MagicMock(role_name="机械工程师")
    member1.is_lead = False
    member1.is_active = True
    member1.allocation_pct = 100
    member1.project_id = 10
    member1.project = MagicMock(project_code="P010", project_name="项目A")

    member2 = MagicMock()
    member2.user_id = 1  # 同一用户
    member2.user = user
    member2.role_code = "ME"
    member2.role_type = MagicMock(role_name="机械工程师")
    member2.is_lead = False
    member2.is_active = True
    member2.allocation_pct = 50
    member2.project_id = 11
    member2.project = MagicMock(project_code="P011", project_name="项目B")

    db.query.return_value.filter.return_value.all.return_value = [member1, member2]

    result = get_project_members_for_ticket(db, project_ids=[10, 11])
    assert len(result) == 1  # 去重后只有1人
    assert len(result[0]["projects"]) == 2  # 参与2个项目


def test_get_members_sorted_by_role():
    db = _make_db()

    def make_member(uid, role_code, real_name):
        user = MagicMock()
        user.username = real_name
        user.real_name = real_name
        user.email = None
        user.phone = None
        user.department = None
        user.position = None
        m = MagicMock()
        m.user_id = uid
        m.user = user
        m.role_code = role_code
        m.role_type = MagicMock(role_name=role_code)
        m.is_lead = False
        m.is_active = True
        m.allocation_pct = 100
        m.project_id = 1
        m.project = MagicMock(project_code="P1", project_name="项目X")
        return m

    members = [
        make_member(2, "QA", "赵六"),
        make_member(1, "PM", "张三"),
    ]
    db.query.return_value.filter.return_value.all.return_value = members
    result = get_project_members_for_ticket(db, project_ids=[1])
    assert result[0]["role_code"] == "PM"  # PM优先级最高


# ---------- get_ticket_related_projects ----------

def test_get_ticket_related_projects_not_found():
    db = _make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    result = get_ticket_related_projects(db, ticket_id=999)
    assert result["primary_project"] is None
    assert result["related_projects"] == []


def test_get_ticket_related_projects_with_data():
    db = _make_db()

    ticket = MagicMock()
    ticket.project_id = 5

    project = MagicMock()
    project.id = 5
    project.project_code = "P005"
    project.project_name = "主项目"

    # ServiceTicket/ServiceTicketProject are imported inside the function; patch at source
    ServiceTicket_mock = MagicMock()
    ServiceTicketProject_mock = MagicMock()

    def query_side(model):
        q = MagicMock()
        if model is ServiceTicket_mock:
            q.filter.return_value.first.return_value = ticket
        elif model is ServiceTicketProject_mock:
            q.filter.return_value.all.return_value = []
        else:
            q.filter.return_value.first.return_value = project
        return q

    db.query.side_effect = query_side

    with patch("app.models.service.ServiceTicket", ServiceTicket_mock), \
         patch("app.models.service.ServiceTicketProject", ServiceTicketProject_mock):
        result = get_ticket_related_projects(db, ticket_id=1)

    # 主要验证函数能正常执行并返回字典结构
    assert "primary_project" in result
    assert "related_projects" in result
