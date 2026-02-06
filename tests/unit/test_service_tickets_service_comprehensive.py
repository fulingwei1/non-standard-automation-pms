# -*- coding: utf-8 -*-
"""
ServiceTicketsService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- get_dashboard_statistics: 获取仪表板统计
- get_project_members: 获取项目成员
- get_ticket_projects: 获取工单关联项目
- get_ticket_statistics: 获取工单统计
- get_service_tickets: 获取服务工单列表
- get_service_ticket: 获取单个服务工单
- create_service_ticket: 创建服务工单
- assign_ticket: 分配服务工单
- update_ticket_status: 更新工单状态
- close_ticket: 关闭服务工单
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException


class TestServiceTicketsServiceInit:
    """测试 ServiceTicketsService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        service = ServiceTicketsService(mock_db)

        assert service.db == mock_db


class TestGetDashboardStatistics:
    """测试 get_dashboard_statistics 方法"""

    def test_returns_statistics(self):
        """测试返回仪表板统计"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)
        service._calculate_avg_response_time = MagicMock(return_value=30.0)
        service._calculate_satisfaction_rate = MagicMock(return_value=4.5)

        result = service.get_dashboard_statistics()

        assert result is not None
        assert hasattr(result, 'today_new_tickets')
        assert hasattr(result, 'pending_tickets')

    def test_counts_today_tickets(self):
        """测试统计今日工单"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)
        service._calculate_avg_response_time = MagicMock(return_value=0)
        service._calculate_satisfaction_rate = MagicMock(return_value=0)

        result = service.get_dashboard_statistics()

        assert result.today_new_tickets == 10


class TestGetProjectMembers:
    """测试 get_project_members 方法"""

    def test_returns_members_dict(self):
        """测试返回成员字典"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user1.name = "张三"
        mock_user1.department = MagicMock()
        mock_user1.department.name = "服务部"
        mock_user1.position = "工程师"
        mock_user1.phone = "13800138000"

        mock_user2 = MagicMock()
        mock_user2.id = 2
        mock_user2.name = "李四"
        mock_user2.department = None
        mock_user2.position = "技术员"
        mock_user2.phone = "13900139000"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_user1, mock_user2]
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service.get_project_members()

        assert "members" in result
        assert len(result["members"]) == 2
        assert result["members"][0]["name"] == "张三"

    def test_handles_no_department(self):
        """测试处理无部门情况"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.name = "王五"
        mock_user.department = None
        mock_user.position = "实习生"
        mock_user.phone = "13700137000"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_user]
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service.get_project_members()

        assert result["members"][0]["department"] is None


class TestGetTicketProjects:
    """测试 get_ticket_projects 方法"""

    def test_returns_projects(self):
        """测试返回关联项目"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.name = "项目A"
        mock_project1.status = "进行中"

        mock_ticket = MagicMock()
        mock_ticket.projects = [mock_project1]

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_ticket
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service.get_ticket_projects(1)

        assert "projects" in result
        assert len(result["projects"]) == 1
        assert result["projects"][0]["name"] == "项目A"

    def test_raises_for_missing_ticket(self):
        """测试工单不存在时抛出异常"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        with pytest.raises(HTTPException) as exc_info:
            service.get_ticket_projects(999)

        assert exc_info.value.status_code == 404


class TestGetTicketStatistics:
    """测试 get_ticket_statistics 方法"""

    def test_returns_statistics_dict(self):
        """测试返回统计字典"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 50
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service.get_ticket_statistics()

        assert "total_tickets" in result
        assert result["total_tickets"] == 50

    def test_filters_by_date_range(self):
        """测试按日期范围过滤"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 20
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service.get_ticket_statistics(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        assert result is not None
        mock_query.filter.assert_called()

    def test_filters_by_status(self):
        """测试按状态过滤"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service.get_ticket_statistics(status="pending")

        assert result is not None

    def test_calculates_completion_rate(self):
        """测试计算完成率"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_status_stat = MagicMock()
        mock_status_stat.status = "completed"
        mock_status_stat.count = 20

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [mock_status_stat]
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service.get_ticket_statistics()

        assert "completion_rate" in result


class TestGetServiceTickets:
    """测试 get_service_tickets 方法"""

    def test_returns_paginated_list(self):
        """测试返回分页列表"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_ticket1 = MagicMock()
        mock_ticket1.id = 1
        mock_ticket2 = MagicMock()
        mock_ticket2.id = 2

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_ticket1, mock_ticket2]
        mock_query.count.return_value = 2
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        with patch('app.services.service.service_tickets_service.ServiceTicketResponse') as mock_response:
            mock_response.model_validate.side_effect = lambda x: x
            result = service.get_service_tickets(page=1, page_size=20)

        assert result is not None

    def test_filters_by_keyword(self):
        """测试按关键字过滤"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        with patch('app.services.service.service_tickets_service.ServiceTicketResponse') as mock_response:
            result = service.get_service_tickets(keyword="设备故障")

        mock_query.filter.assert_called()

    def test_filters_by_priority(self):
        """测试按优先级过滤"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        with patch('app.services.service.service_tickets_service.ServiceTicketResponse') as mock_response:
            result = service.get_service_tickets(priority="high")

        mock_query.filter.assert_called()

    def test_filters_by_customer_id(self):
        """测试按客户ID过滤"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        with patch('app.services.service.service_tickets_service.ServiceTicketResponse') as mock_response:
            result = service.get_service_tickets(customer_id=1)

        mock_query.filter.assert_called()


class TestGetServiceTicket:
    """测试 get_service_ticket 方法"""

    def test_returns_ticket(self):
        """测试返回服务工单"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.title = "设备维修"

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_ticket
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service.get_service_ticket(1)

        assert result == mock_ticket

    def test_returns_none_for_missing(self):
        """测试工单不存在时返回None"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service.get_service_ticket(999)

        assert result is None


class TestCreateServiceTicket:
    """测试 create_service_ticket 方法"""

    def test_creates_ticket_successfully(self):
        """测试成功创建服务工单"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)
        service._auto_assign_ticket = MagicMock()
        service._send_ticket_notification = MagicMock()

        ticket_data = MagicMock()
        ticket_data.ticket_type = "maintenance"
        ticket_data.title = "设备定期维护"
        ticket_data.description = "定期维护检查"
        ticket_data.priority = "medium"
        ticket_data.customer_id = 1
        ticket_data.project_id = 1
        ticket_data.contact_person = "张三"
        ticket_data.contact_phone = "13800138000"
        ticket_data.contact_email = "test@example.com"
        ticket_data.service_location = "工厂A"
        ticket_data.expected_resolution_time = None

        current_user = MagicMock()
        current_user.id = 1

        result = service.create_service_ticket(ticket_data, current_user)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_generates_ticket_number(self):
        """测试生成工单编号"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service._generate_ticket_number("maintenance")

        assert result.startswith("MAINT")
        assert "0004" in result


class TestAssignTicket:
    """测试 assign_ticket 方法"""

    def test_assigns_successfully(self):
        """测试成功分配工单"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.assigned_to = None

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_ticket
        mock_db.query.return_value = mock_query
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ServiceTicketsService(mock_db)
        service._send_ticket_notification = MagicMock()

        assign_data = MagicMock()
        assign_data.assigned_to = 5
        assign_data.note = "请尽快处理"

        current_user = MagicMock()
        current_user.id = 1

        result = service.assign_ticket(1, assign_data, current_user)

        assert mock_ticket.assigned_to == 5
        assert mock_ticket.status == "assigned"
        mock_db.commit.assert_called_once()

    def test_returns_none_for_missing(self):
        """测试工单不存在时返回None"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        assign_data = MagicMock()
        assign_data.assigned_to = 5

        current_user = MagicMock()
        current_user.id = 1

        result = service.assign_ticket(999, assign_data, current_user)

        assert result is None


class TestUpdateTicketStatus:
    """测试 update_ticket_status 方法"""

    def test_updates_status_successfully(self):
        """测试成功更新状态"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.status = "pending"

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_ticket
        mock_db.query.return_value = mock_query
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ServiceTicketsService(mock_db)
        service._send_ticket_notification = MagicMock()

        current_user = MagicMock()
        current_user.id = 1

        result = service.update_ticket_status(1, "in_progress", "开始处理", current_user)

        assert mock_ticket.status == "in_progress"
        mock_db.commit.assert_called_once()

    def test_sets_resolved_at_on_completion(self):
        """测试完成时设置解决时间"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.status = "in_progress"
        mock_ticket.resolved_at = None

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_ticket
        mock_db.query.return_value = mock_query
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ServiceTicketsService(mock_db)
        service._send_ticket_notification = MagicMock()

        current_user = MagicMock()
        current_user.id = 1

        result = service.update_ticket_status(1, "completed", "问题已解决", current_user)

        assert mock_ticket.status == "completed"
        assert mock_ticket.resolved_at is not None

    def test_sets_started_at_on_in_progress(self):
        """测试开始处理时设置开始时间"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.status = "pending"
        mock_ticket.started_at = None

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_ticket
        mock_db.query.return_value = mock_query
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ServiceTicketsService(mock_db)
        service._send_ticket_notification = MagicMock()

        current_user = MagicMock()
        current_user.id = 1

        result = service.update_ticket_status(1, "in_progress", None, current_user)

        assert mock_ticket.started_at is not None

    def test_returns_none_for_missing(self):
        """测试工单不存在时返回None"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        current_user = MagicMock()
        current_user.id = 1

        result = service.update_ticket_status(999, "in_progress", None, current_user)

        assert result is None


class TestCloseTicket:
    """测试 close_ticket 方法"""

    def test_closes_ticket_successfully(self):
        """测试成功关闭工单"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.status = "in_progress"

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_ticket
        mock_db.query.return_value = mock_query
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ServiceTicketsService(mock_db)
        service._send_ticket_notification = MagicMock()
        service._create_satisfaction_survey = MagicMock()

        close_data = MagicMock()
        close_data.resolution_summary = "更换了损坏的零件"
        close_data.customer_feedback = "客户表示满意"
        close_data.customer_satisfaction = 5

        current_user = MagicMock()
        current_user.id = 1

        result = service.close_ticket(1, close_data, current_user)

        assert mock_ticket.status == "completed"
        assert mock_ticket.resolution_summary == "更换了损坏的零件"
        mock_db.commit.assert_called_once()

    def test_sets_resolved_at(self):
        """测试设置解决时间"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.status = "in_progress"
        mock_ticket.resolved_at = None

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_ticket
        mock_db.query.return_value = mock_query
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = ServiceTicketsService(mock_db)
        service._send_ticket_notification = MagicMock()
        service._create_satisfaction_survey = MagicMock()

        close_data = MagicMock()
        close_data.resolution_summary = "已解决"
        close_data.customer_feedback = None
        close_data.customer_satisfaction = 4

        current_user = MagicMock()
        current_user.id = 1

        result = service.close_ticket(1, close_data, current_user)

        assert mock_ticket.resolved_at is not None

    def test_returns_none_for_missing(self):
        """测试工单不存在时返回None"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        close_data = MagicMock()
        close_data.resolution_summary = "已解决"

        current_user = MagicMock()
        current_user.id = 1

        result = service.close_ticket(999, close_data, current_user)

        assert result is None


class TestGenerateTicketNumber:
    """测试 _generate_ticket_number 方法"""

    def test_generates_installation_number(self):
        """测试生成安装工单编号"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service._generate_ticket_number("installation")

        assert result.startswith("INST")
        assert "0001" in result

    def test_generates_repair_number(self):
        """测试生成维修工单编号"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service._generate_ticket_number("repair")

        assert result.startswith("REPAIR")
        assert "0011" in result

    def test_handles_unknown_type(self):
        """测试处理未知类型"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service._generate_ticket_number("unknown_type")

        assert result.startswith("SRV")


class TestCalculateAvgResponseTime:
    """测试 _calculate_avg_response_time 方法"""

    def test_returns_zero_for_no_data(self):
        """测试无数据时返回零"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service._calculate_avg_response_time()

        assert result == 0

    def test_calculates_average(self):
        """测试计算平均值"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        # 模拟返回的响应时间（秒）
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.all.return_value = [(1800,), (3600,)]  # 30分钟和60分钟
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service._calculate_avg_response_time()

        # (1800 + 3600) / 2 / 60 = 45 分钟
        assert result == 45.0


class TestCalculateSatisfactionRate:
    """测试 _calculate_satisfaction_rate 方法"""

    def test_returns_zero_for_no_data(self):
        """测试无数据时返回零"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service._calculate_satisfaction_rate()

        assert result == 0

    def test_calculates_average_rating(self):
        """测试计算平均评分"""
        from app.services.service.service_tickets_service import ServiceTicketsService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.all.return_value = [(4,), (5,), (4,)]
        mock_db.query.return_value = mock_query

        service = ServiceTicketsService(mock_db)

        result = service._calculate_satisfaction_rate()

        # (4 + 5 + 4) / 3 = 4.33
        assert result == 4.33
