# -*- coding: utf-8 -*-
"""第九批: test_service_tickets_service_cov9.py - ServiceTicketsService 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime

pytest.importorskip("app.services.service.service_tickets_service")

from app.services.service.service_tickets_service import ServiceTicketsService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return ServiceTicketsService(db=mock_db)


def make_ticket(id=1, status="PENDING", ticket_no="ST-0001"):
    t = MagicMock()
    t.id = id
    t.status = status
    t.ticket_no = ticket_no
    t.ticket_type = "maintenance"
    t.created_at = datetime.now()
    t.resolved_at = None
    return t


class TestServiceTicketsServiceInit:
    def test_init(self, service, mock_db):
        assert service.db is mock_db


class TestGetDashboardStatistics:
    """测试仪表板统计"""

    def test_get_dashboard_statistics(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.count.return_value = 10
        with patch.object(service, "_calculate_avg_response_time", return_value=2.5):
            with patch.object(service, "_calculate_satisfaction_rate", return_value=0.9):
                result = service.get_dashboard_statistics()
                assert result is not None


class TestGetServiceTickets:
    """测试工单列表查询"""

    def test_get_service_tickets_no_filter(self, service, mock_db):
        mock_q = MagicMock()
        mock_db.query.return_value.options.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.count.return_value = 0
        mock_q.offset.return_value.limit.return_value.all.return_value = []
        result = service.get_service_tickets()
        assert result is not None

    def test_get_service_tickets_with_status(self, service, mock_db):
        mock_q = MagicMock()
        mock_db.query.return_value.options.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.count.return_value = 2
        mock_q.offset.return_value.limit.return_value.all.return_value = [make_ticket(), make_ticket(id=2)]
        result = service.get_service_tickets(status="PENDING")
        assert result is not None


class TestGetServiceTicket:
    """测试工单详情"""

    def test_get_service_ticket_found(self, service, mock_db):
        ticket = make_ticket()
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = ticket
        result = service.get_service_ticket(ticket_id=1)
        assert result is not None

    def test_get_service_ticket_not_found(self, service, mock_db):
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        result = service.get_service_ticket(ticket_id=9999)
        assert result is None


class TestCreateServiceTicket:
    """测试创建工单"""

    def test_create_service_ticket(self, service, mock_db):
        ticket_data = MagicMock()
        ticket_data.ticket_type = "maintenance"
        ticket_data.problem_type = "mechanical"
        ticket_data.problem_desc = "设备故障"
        ticket_data.urgency = "NORMAL"
        ticket_data.priority = None
        ticket_data.customer_id = 1
        ticket_data.project_id = None
        ticket_data.reported_by = "张三"
        ticket_data.reported_time = None

        mock_db.query.return_value.filter.return_value.count.return_value = 0

        with patch("app.utils.db_helpers.save_obj"):
            with patch.object(service, "_auto_assign_ticket"):
                with patch.object(service, "_send_ticket_notification"):
                    result = service.create_service_ticket(ticket_data=ticket_data)
                    assert result is not None


class TestCloseTicket:
    """测试关闭工单"""

    def test_close_ticket(self, service, mock_db):
        ticket = make_ticket(status="IN_PROGRESS")
        # get_service_ticket uses options().filter().first()
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = ticket
        close_data = MagicMock()
        close_data.resolution_summary = "已修复"
        close_data.solution = "更换零件"
        close_data.customer_feedback = "满意"
        close_data.customer_satisfaction = 5

        with patch.object(service, "_send_ticket_notification"):
            with patch.object(service, "_create_satisfaction_survey"):
                result = service.close_ticket(ticket_id=1, close_data=close_data)
                assert result is not None


class TestGenerateTicketNumber:
    """测试工单编号生成"""

    def test_generate_ticket_number_maintenance(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.count.return_value = 3
        result = service._generate_ticket_number("maintenance")
        assert "MAINT" in result

    def test_generate_ticket_number_unknown_type(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        result = service._generate_ticket_number("unknown_type")
        assert isinstance(result, str)
