# -*- coding: utf-8 -*-
"""
ITR服务单元测试
测试工单、问题、验收端到端流程视图
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.acceptance import AcceptanceOrder
from app.models.issue import Issue
from app.models.service import ServiceTicket
from app.models.sla import SLAMonitor
from app.services.itr_service import (
    get_ticket_timeline,
    get_issue_related_data,
    get_itr_dashboard_data,
)


class TestGetTicketTimeline:
    """测试获取工单时间线"""

    def test_ticket_not_found(self):
        """测试工单不存在时返回None"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_ticket_timeline(mock_db, ticket_id=999)

        assert result is None

    def test_ticket_with_empty_timeline(self):
        """测试工单无时间线数据"""
        mock_db = MagicMock(spec=Session)

        mock_ticket = Mock(spec=ServiceTicket)
        mock_ticket.id = 1
        mock_ticket.ticket_no = "TK-001"
        mock_ticket.project_id = 1
        mock_ticket.timeline = None

        # 设置各个查询返回
        query_ticket = MagicMock()
        query_ticket.filter.return_value.first.return_value = mock_ticket

        query_issues = MagicMock()
        query_issues.filter.return_value.order_by.return_value.all.return_value = []

        query_acceptance = MagicMock()
        query_acceptance.filter.return_value.order_by.return_value.all.return_value = []

        query_sla = MagicMock()
        query_sla.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [query_ticket, query_issues, query_acceptance, query_sla]

        result = get_ticket_timeline(mock_db, ticket_id=1)

        assert result is not None
        assert result['ticket_id'] == 1
        assert result['ticket_no'] == "TK-001"
        assert result['timeline'] == []

    def test_ticket_with_timeline_events(self):
        """测试工单包含时间线事件"""
        mock_db = MagicMock(spec=Session)

        mock_ticket = Mock(spec=ServiceTicket)
        mock_ticket.id = 1
        mock_ticket.ticket_no = "TK-001"
        mock_ticket.project_id = 1
        mock_ticket.timeline = [
            {
                "type": "STATUS_CHANGE",
                "timestamp": "2024-01-15T10:00:00",
                "user": "admin",
                "description": "状态变更为处理中"
            }
        ]

        query_ticket = MagicMock()
        query_ticket.filter.return_value.first.return_value = mock_ticket

        query_issues = MagicMock()
        query_issues.filter.return_value.order_by.return_value.all.return_value = []

        query_acceptance = MagicMock()
        query_acceptance.filter.return_value.order_by.return_value.all.return_value = []

        query_sla = MagicMock()
        query_sla.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [query_ticket, query_issues, query_acceptance, query_sla]

        result = get_ticket_timeline(mock_db, ticket_id=1)

        assert len(result['timeline']) >= 1
        assert result['timeline'][0]['type'] == "TICKET"
        assert result['timeline'][0]['event_type'] == "STATUS_CHANGE"

    def test_ticket_with_related_issues(self):
        """测试工单包含关联问题"""
        mock_db = MagicMock(spec=Session)

        mock_ticket = Mock(spec=ServiceTicket)
        mock_ticket.id = 1
        mock_ticket.ticket_no = "TK-001"
        mock_ticket.project_id = 1
        mock_ticket.timeline = None

        mock_issue = Mock(spec=Issue)
        mock_issue.id = 10
        mock_issue.issue_no = "ISS-001"
        mock_issue.title = "测试问题"
        mock_issue.report_date = datetime(2024, 1, 15, 10, 0, 0)
        mock_issue.reporter_name = "reporter"
        mock_issue.resolved_at = None

        # 第一次查询返回工单
        query_ticket = MagicMock()
        query_ticket.filter.return_value.first.return_value = mock_ticket

        # 第二次查询返回问题列表
        query_issues = MagicMock()
        query_issues.filter.return_value.order_by.return_value.all.return_value = [mock_issue]

        # 第三次查询返回验收单列表
        query_acceptance = MagicMock()
        query_acceptance.filter.return_value.order_by.return_value.all.return_value = []

        # 第四次查询返回SLA监控
        query_sla = MagicMock()
        query_sla.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [query_ticket, query_issues, query_acceptance, query_sla]

        result = get_ticket_timeline(mock_db, ticket_id=1)

        assert result['total_events'] >= 1

    def test_ticket_with_sla_monitor(self):
        """测试工单包含SLA监控"""
        mock_db = MagicMock(spec=Session)

        mock_ticket = Mock(spec=ServiceTicket)
        mock_ticket.id = 1
        mock_ticket.ticket_no = "TK-001"
        mock_ticket.project_id = 1
        mock_ticket.timeline = None

        mock_sla = Mock(spec=SLAMonitor)
        mock_sla.created_at = datetime(2024, 1, 15, 10, 0, 0)
        mock_sla.response_deadline = datetime(2024, 1, 15, 14, 0, 0)
        mock_sla.resolve_deadline = datetime(2024, 1, 16, 18, 0, 0)
        mock_sla.actual_response_time = datetime(2024, 1, 15, 12, 0, 0)
        mock_sla.actual_resolve_time = None
        mock_sla.response_status = "ON_TIME"
        mock_sla.resolve_status = None
        mock_sla.policy = Mock()
        mock_sla.policy.policy_name = "标准SLA"

        # 配置查询链
        query_ticket = MagicMock()
        query_ticket.filter.return_value.first.return_value = mock_ticket

        query_issues = MagicMock()
        query_issues.filter.return_value.order_by.return_value.all.return_value = []

        query_acceptance = MagicMock()
        query_acceptance.filter.return_value.order_by.return_value.all.return_value = []

        query_sla = MagicMock()
        query_sla.filter.return_value.first.return_value = mock_sla

        mock_db.query.side_effect = [query_ticket, query_issues, query_acceptance, query_sla]

        result = get_ticket_timeline(mock_db, ticket_id=1)

        # 应该有SLA相关事件
        sla_events = [e for e in result['timeline'] if e['type'] == 'SLA']
        assert len(sla_events) >= 1


class TestGetIssueRelatedData:
    """测试获取问题关联数据"""

    def test_issue_not_found(self):
        """测试问题不存在时返回None"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_issue_related_data(mock_db, issue_id=999)

        assert result is None

    def test_issue_with_no_related_data(self):
        """测试问题无关联数据"""
        mock_db = MagicMock(spec=Session)

        mock_issue = Mock(spec=Issue)
        mock_issue.id = 1
        mock_issue.issue_no = "ISS-001"
        mock_issue.title = "测试问题"
        mock_issue.status = "OPEN"
        mock_issue.category = "CUSTOMER"
        mock_issue.project_id = None
        mock_issue.acceptance_order_id = None
        mock_issue.related_issue_id = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_issue
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_issue_related_data(mock_db, issue_id=1)

        assert result is not None
        assert result['issue']['id'] == 1
        assert result['issue']['issue_no'] == "ISS-001"
        assert result['related_tickets'] == []
        assert result['related_acceptance'] == []
        assert result['related_issues'] == []

    def test_issue_with_related_tickets(self):
        """测试问题有关联工单"""
        mock_db = MagicMock(spec=Session)

        mock_issue = Mock(spec=Issue)
        mock_issue.id = 1
        mock_issue.issue_no = "ISS-001"
        mock_issue.title = "测试问题"
        mock_issue.status = "OPEN"
        mock_issue.category = "CUSTOMER"
        mock_issue.project_id = 1
        mock_issue.acceptance_order_id = None
        mock_issue.related_issue_id = None

        mock_ticket = Mock(spec=ServiceTicket)
        mock_ticket.id = 10
        mock_ticket.ticket_no = "TK-001"
        mock_ticket.problem_type = "DEFECT"
        mock_ticket.urgency = "HIGH"
        mock_ticket.status = "IN_PROGRESS"
        mock_ticket.reported_time = datetime(2024, 1, 15)

        # 第一次查询返回问题
        query_issue = MagicMock()
        query_issue.filter.return_value.first.return_value = mock_issue

        # 第二次查询返回工单列表
        query_tickets = MagicMock()
        query_tickets.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_ticket]

        # 第三次查询返回验收单
        query_acceptance = MagicMock()
        query_acceptance.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        # 第四次查询返回子问题
        query_children = MagicMock()
        query_children.filter.return_value.all.return_value = []

        mock_db.query.side_effect = [query_issue, query_tickets, query_acceptance, query_children]

        result = get_issue_related_data(mock_db, issue_id=1)

        assert len(result['related_tickets']) == 1
        assert result['related_tickets'][0]['ticket_no'] == "TK-001"

    def test_issue_with_acceptance_order_id(self):
        """测试问题直接关联验收单ID"""
        mock_db = MagicMock(spec=Session)

        mock_issue = Mock(spec=Issue)
        mock_issue.id = 1
        mock_issue.issue_no = "ISS-001"
        mock_issue.title = "测试问题"
        mock_issue.status = "OPEN"
        mock_issue.category = "CUSTOMER"
        mock_issue.project_id = 1
        mock_issue.acceptance_order_id = 5
        mock_issue.related_issue_id = None

        mock_order = Mock(spec=AcceptanceOrder)
        mock_order.id = 5
        mock_order.order_no = "ACC-001"
        mock_order.acceptance_type = "FAT"
        mock_order.status = "PENDING"
        mock_order.overall_result = None

        # 配置查询链
        query_issue = MagicMock()
        query_issue.filter.return_value.first.return_value = mock_issue

        query_tickets = MagicMock()
        query_tickets.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        query_order = MagicMock()
        query_order.filter.return_value.first.return_value = mock_order

        query_children = MagicMock()
        query_children.filter.return_value.all.return_value = []

        mock_db.query.side_effect = [query_issue, query_tickets, query_order, query_children]

        result = get_issue_related_data(mock_db, issue_id=1)

        assert len(result['related_acceptance']) == 1
        assert result['related_acceptance'][0]['order_no'] == "ACC-001"

    def test_issue_with_parent_issue(self):
        """测试问题有父问题"""
        mock_db = MagicMock(spec=Session)

        mock_issue = Mock(spec=Issue)
        mock_issue.id = 1
        mock_issue.issue_no = "ISS-001"
        mock_issue.title = "子问题"
        mock_issue.status = "OPEN"
        mock_issue.category = "CUSTOMER"
        mock_issue.project_id = None
        mock_issue.acceptance_order_id = None
        mock_issue.related_issue_id = 100  # 父问题ID

        mock_parent_issue = Mock(spec=Issue)
        mock_parent_issue.id = 100
        mock_parent_issue.issue_no = "ISS-000"
        mock_parent_issue.title = "父问题"
        mock_parent_issue.status = "OPEN"

        # 配置查询链
        query_issue = MagicMock()
        query_issue.filter.return_value.first.return_value = mock_issue

        query_parent = MagicMock()
        query_parent.filter.return_value.first.return_value = mock_parent_issue

        query_children = MagicMock()
        query_children.filter.return_value.all.return_value = []

        mock_db.query.side_effect = [query_issue, query_parent, query_children]

        result = get_issue_related_data(mock_db, issue_id=1)

        assert len(result['related_issues']) == 1
        assert result['related_issues'][0]['issue_no'] == "ISS-000"
        assert result['related_issues'][0]['relation'] == "parent"


class TestGetItrDashboardData:
    """测试获取ITR看板数据"""

    def test_dashboard_empty_data(self):
        """测试无数据时的看板"""
        mock_db = MagicMock(spec=Session)

        # 所有count返回0
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        result = get_itr_dashboard_data(mock_db)

        assert result['tickets']['total'] == 0
        assert result['issues']['total'] == 0
        assert result['acceptance']['total'] == 0
        assert result['sla']['total'] == 0
        assert result['sla']['response_rate'] == 0
        assert result['sla']['resolve_rate'] == 0

    def test_dashboard_with_project_filter(self):
        """测试按项目筛选的看板"""
        mock_db = MagicMock(spec=Session)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.count.return_value = 5
        mock_db.query.return_value = mock_query

        result = get_itr_dashboard_data(mock_db, project_id=1)

        # 验证filter被调用（项目筛选）
        assert mock_query.filter.called

    def test_dashboard_with_date_range(self):
        """测试按日期范围筛选的看板"""
        mock_db = MagicMock(spec=Session)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.count.return_value = 10
        mock_db.query.return_value = mock_query

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        result = get_itr_dashboard_data(mock_db, start_date=start_date, end_date=end_date)

        # 验证filter被调用（日期筛选）
        assert mock_query.filter.called

    def test_dashboard_sla_rates_calculation(self):
        """测试SLA达成率计算"""
        mock_db = MagicMock(spec=Session)

        # 简化的mock - 所有查询返回相同的mock
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.count.return_value = 10

        mock_db.query.return_value = mock_query

        result = get_itr_dashboard_data(mock_db)

        # 验证结构完整
        assert 'tickets' in result
        assert 'issues' in result
        assert 'acceptance' in result
        assert 'sla' in result
        # 当total > 0 时，rate应该是100%
        assert result['sla']['response_rate'] == 100.0
        assert result['sla']['resolve_rate'] == 100.0

    def test_dashboard_ticket_status_breakdown(self):
        """测试工单状态分布"""
        mock_db = MagicMock(spec=Session)

        # 工单查询返回不同状态的计数
        ticket_query = MagicMock()
        ticket_query.filter.return_value = ticket_query

        # total=100, pending=20, in_progress=30, resolved=40, closed=10
        counts = [100, 20, 30, 40, 10]
        count_idx = [0]

        def ticket_count():
            idx = count_idx[0]
            count_idx[0] += 1
            return counts[idx] if idx < len(counts) else 0

        ticket_query.count.side_effect = ticket_count

        # 其他查询返回0
        other_query = MagicMock()
        other_query.filter.return_value = other_query
        other_query.join.return_value = other_query
        other_query.count.return_value = 0

        mock_db.query.side_effect = [
            ticket_query,  # 工单查询
            other_query, other_query, other_query, other_query, other_query,
            other_query, other_query, other_query, other_query, other_query,
            other_query, other_query, other_query
        ]

        result = get_itr_dashboard_data(mock_db)

        assert result['tickets']['total'] == 100
        assert result['tickets']['pending'] == 20
        assert result['tickets']['in_progress'] == 30
        assert result['tickets']['resolved'] == 40
        assert result['tickets']['closed'] == 10


class TestIntegration:
    """集成测试场景"""

    def test_full_ticket_lifecycle_timeline(self):
        """测试完整工单生命周期时间线"""
        mock_db = MagicMock(spec=Session)

        # 创建完整的工单数据
        mock_ticket = Mock(spec=ServiceTicket)
        mock_ticket.id = 1
        mock_ticket.ticket_no = "TK-001"
        mock_ticket.project_id = 1
        mock_ticket.timeline = [
            {"type": "CREATED", "timestamp": "2024-01-15T09:00:00", "user": "user1", "description": "工单创建"},
            {"type": "ASSIGNED", "timestamp": "2024-01-15T09:30:00", "user": "admin", "description": "分配给工程师"},
            {"type": "RESOLVED", "timestamp": "2024-01-15T17:00:00", "user": "engineer", "description": "问题已解决"},
        ]

        # 关联问题
        mock_issue = Mock(spec=Issue)
        mock_issue.id = 10
        mock_issue.issue_no = "ISS-001"
        mock_issue.title = "关联问题"
        mock_issue.report_date = datetime(2024, 1, 15, 10, 0, 0)
        mock_issue.reporter_name = "reporter"
        mock_issue.resolved_at = datetime(2024, 1, 15, 16, 0, 0)
        mock_issue.resolved_by_name = "resolver"

        # 验收单
        mock_order = Mock(spec=AcceptanceOrder)
        mock_order.id = 20
        mock_order.order_no = "ACC-001"
        mock_order.acceptance_type = "FAT"
        mock_order.created_at = datetime(2024, 1, 14)
        mock_order.customer_signed_at = datetime(2024, 1, 16)
        mock_order.customer_signer = "customer"

        # 配置查询
        query_ticket = MagicMock()
        query_ticket.filter.return_value.first.return_value = mock_ticket

        query_issues = MagicMock()
        query_issues.filter.return_value.order_by.return_value.all.return_value = [mock_issue]

        query_acceptance = MagicMock()
        query_acceptance.filter.return_value.order_by.return_value.all.return_value = [mock_order]

        query_sla = MagicMock()
        query_sla.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [query_ticket, query_issues, query_acceptance, query_sla]

        result = get_ticket_timeline(mock_db, ticket_id=1)

        # 验证时间线事件数量
        assert result['total_events'] >= 5  # 3 ticket + 2 issue + 2 acceptance events
        # 验证时间线按时间排序
        timestamps = [e.get('timestamp') for e in result['timeline'] if e.get('timestamp')]
        assert timestamps == sorted(timestamps)
