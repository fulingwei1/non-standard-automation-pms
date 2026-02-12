# -*- coding: utf-8 -*-
"""服务工单服务单元测试"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

from fastapi import HTTPException
from app.services.service.service_tickets_service import ServiceTicketsService


def _make_db():
    return MagicMock()


def _make_user(uid=1):
    u = MagicMock()
    u.id = uid
    u.name = "测试用户"
    u.is_active = True
    u.department = "工程部"
    u.position = "工程师"
    u.phone = "13800138000"
    return u


def _make_ticket(**kw):
    t = MagicMock()
    defaults = dict(
        id=1, ticket_no="SRV20250501001", status="PENDING",
        priority="HIGH", ticket_type="repair",
        problem_type="repair", problem_desc="设备故障",
        customer_id=1, project_id=1,
        customer=MagicMock(), projects=[],
        assigned_to=None, assigned_to_id=None,
        assigned_time=None, resolved_at=None, resolved_time=None,
        started_at=None, resolution_summary=None, solution=None,
        customer_feedback=None, customer_satisfaction=None,
        created_at=datetime(2025, 5, 1), updated_at=None,
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(t, k, v)
    return t


class TestGetDashboardStatistics:
    def test_returns_stats(self):
        db = _make_db()
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.with_entities.return_value.all.return_value = []
        svc = ServiceTicketsService(db)
        with patch.object(svc, "_calculate_avg_response_time", return_value=0.0), \
             patch.object(svc, "_calculate_satisfaction_rate", return_value=0.0):
            result = svc.get_dashboard_statistics()
        assert result.active_cases == 0
        assert result.pending_cases == 0


class TestGetProjectMembers:
    def test_returns_members(self):
        db = _make_db()
        user = _make_user()
        db.query.return_value.filter.return_value.all.return_value = [user]
        svc = ServiceTicketsService(db)
        result = svc.get_project_members()
        assert len(result["members"]) == 1


class TestGetTicketProjects:
    def test_found(self):
        db = _make_db()
        ticket = _make_ticket(projects=[MagicMock(id=1, name="项目A", status="active")])
        db.query.return_value.filter.return_value.first.return_value = ticket
        svc = ServiceTicketsService(db)
        result = svc.get_ticket_projects(1)
        assert len(result["projects"]) == 1

    def test_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = ServiceTicketsService(db)
        with pytest.raises(HTTPException):
            svc.get_ticket_projects(999)


class TestGetTicketStatistics:
    def test_basic(self):
        db = _make_db()
        q = db.query.return_value
        q.count.return_value = 5
        q.with_entities.return_value.group_by.return_value.all.return_value = []
        q.filter.return_value.all.return_value = []
        q.filter.return_value.count.return_value = 5
        q.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = []
        svc = ServiceTicketsService(db)
        result = svc.get_ticket_statistics()
        assert "total_tickets" in result


class TestGetServiceTickets:
    def test_list(self):
        db = _make_db()
        q = db.query.return_value.options.return_value
        for attr in ('filter', 'order_by'):
            setattr(q, attr, MagicMock(return_value=q))
        q.count.return_value = 0
        q.all.return_value = []

        with patch("app.services.service.service_tickets_service.apply_keyword_filter", return_value=q), \
             patch("app.services.service.service_tickets_service.get_pagination_params") as gpp, \
             patch("app.services.service.service_tickets_service.apply_pagination", return_value=q):
            pag = MagicMock(page=1, page_size=20, offset=0, limit=20)
            pag.pages_for_total.return_value = 0
            gpp.return_value = pag
            svc = ServiceTicketsService(db)
            result = svc.get_service_tickets()
            assert result.total == 0


class TestGetServiceTicket:
    def test_found(self):
        db = _make_db()
        ticket = _make_ticket()
        db.query.return_value.options.return_value.filter.return_value.first.return_value = ticket
        svc = ServiceTicketsService(db)
        assert svc.get_service_ticket(1) is ticket


class TestCreateServiceTicket:
    def test_create(self):
        db = _make_db()
        db.query.return_value.filter.return_value.count.return_value = 0
        ticket_data = MagicMock(
            ticket_type="repair", problem_type="repair",
            description="故障", problem_desc="故障",
            urgency="NORMAL", priority="HIGH",
            customer_id=1, project_id=1,
            reported_by=None, reported_time=None,
        )
        svc = ServiceTicketsService(db)
        with patch("app.services.service.service_tickets_service.ServiceTicket") as MockTicket:
            instance = _make_ticket()
            MockTicket.return_value = instance
            result = svc.create_service_ticket(ticket_data, _make_user())
        db.add.assert_called_once()
        db.commit.assert_called()


class TestAssignTicket:
    def test_assign(self):
        db = _make_db()
        ticket = _make_ticket()
        svc = ServiceTicketsService(db)
        with patch.object(svc, "get_service_ticket", return_value=ticket):
            assign_data = MagicMock(assigned_to=2, assignee_id=2)
            result = svc.assign_ticket(1, assign_data, _make_user())
        assert ticket.status == "assigned"
        db.commit.assert_called()

    def test_not_found(self):
        db = _make_db()
        svc = ServiceTicketsService(db)
        with patch.object(svc, "get_service_ticket", return_value=None):
            assert svc.assign_ticket(999) is None


class TestUpdateTicketStatus:
    def test_complete(self):
        db = _make_db()
        ticket = _make_ticket(status="IN_PROGRESS")
        svc = ServiceTicketsService(db)
        with patch.object(svc, "get_service_ticket", return_value=ticket):
            result = svc.update_ticket_status(1, "COMPLETED")
        assert ticket.status == "COMPLETED"
        assert ticket.resolved_at is not None

    def test_in_progress(self):
        db = _make_db()
        ticket = _make_ticket(status="PENDING")
        svc = ServiceTicketsService(db)
        with patch.object(svc, "get_service_ticket", return_value=ticket):
            result = svc.update_ticket_status(1, "IN_PROGRESS")
        assert ticket.status == "IN_PROGRESS"
        assert ticket.started_at is not None


class TestCloseTicket:
    def test_close(self):
        db = _make_db()
        ticket = _make_ticket()
        svc = ServiceTicketsService(db)
        with patch.object(svc, "get_service_ticket", return_value=ticket):
            close_data = MagicMock(resolution_summary="已修复", solution="更换零件",
                                   customer_feedback="满意", customer_satisfaction=5, feedback=None, satisfaction=None)
            result = svc.close_ticket(1, close_data, _make_user())
        assert ticket.status == "completed"
        db.commit.assert_called()

    def test_not_found(self):
        db = _make_db()
        svc = ServiceTicketsService(db)
        with patch.object(svc, "get_service_ticket", return_value=None):
            assert svc.close_ticket(999) is None


class TestGenerateTicketNumber:
    def test_format(self):
        db = _make_db()
        db.query.return_value.filter.return_value.count.return_value = 3
        svc = ServiceTicketsService(db)
        num = svc._generate_ticket_number("repair")
        assert num.startswith("REPAIR")
        assert "0004" in num


class TestCalculateAvgResponseTime:
    def test_no_data(self):
        db = _make_db()
        db.query.return_value.filter.return_value.with_entities.return_value.all.return_value = []
        svc = ServiceTicketsService(db)
        assert svc._calculate_avg_response_time() == 0

    def test_with_data(self):
        db = _make_db()
        db.query.return_value.filter.return_value.with_entities.return_value.all.return_value = [(120,), (60,)]
        svc = ServiceTicketsService(db)
        result = svc._calculate_avg_response_time()
        assert result == 1.5  # (120+60)/2 / 60


class TestCalculateSatisfactionRate:
    def test_no_data(self):
        db = _make_db()
        db.query.return_value.filter.return_value.with_entities.return_value.all.return_value = []
        svc = ServiceTicketsService(db)
        assert svc._calculate_satisfaction_rate() == 0
