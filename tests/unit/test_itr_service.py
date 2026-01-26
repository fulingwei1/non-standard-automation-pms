# -*- coding: utf-8 -*-
"""
ITR流程服务单元测试

测试覆盖:
- 获取工单完整时间线
- 获取问题关联数据
- 获取ITR流程看板数据
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.services.itr_service import (
    get_ticket_timeline,
    get_issue_related_data,
    get_itr_dashboard_data,
)


class TestGetTicketTimeline:
    """获取工单时间线测试"""

    def test_get_ticket_timeline_not_found(self, db_session: Session):
        """测试工单不存在时返回None"""
        result = get_ticket_timeline(db_session, ticket_id=99999)
        assert result is None

    def test_get_ticket_timeline_structure(self, db_session: Session):
        """测试返回数据结构（如果工单存在）"""
        result = get_ticket_timeline(db_session, ticket_id=1)
        # 如果工单存在，检查结构
        if result is not None:
            assert 'ticket_id' in result
            assert 'ticket_no' in result
            assert 'timeline' in result
            assert 'total_events' in result
            assert isinstance(result['timeline'], list)


class TestGetIssueRelatedData:
    """获取问题关联数据测试"""

    def test_get_issue_related_data_not_found(self, db_session: Session):
        """测试问题不存在时返回None"""
        result = get_issue_related_data(db_session, issue_id=99999)
        assert result is None

    def test_get_issue_related_data_structure(self, db_session: Session):
        """测试返回数据结构（如果问题存在）"""
        result = get_issue_related_data(db_session, issue_id=1)
        # 如果问题存在，检查结构
        if result is not None:
            assert 'issue' in result
            assert 'related_tickets' in result
            assert 'related_acceptance' in result
            assert 'related_issues' in result


class TestGetItrDashboardData:
    """获取ITR看板数据测试"""

    def test_get_itr_dashboard_data_no_filter(self, db_session: Session):
        """测试无筛选条件获取看板数据"""
        result = get_itr_dashboard_data(db_session)

        assert 'tickets' in result
        assert 'issues' in result
        assert 'acceptance' in result
        assert 'sla' in result

    def test_get_itr_dashboard_data_tickets_structure(self, db_session: Session):
        """测试工单统计结构"""
        result = get_itr_dashboard_data(db_session)
        tickets = result['tickets']

        assert 'total' in tickets
        assert 'pending' in tickets
        assert 'in_progress' in tickets
        assert 'resolved' in tickets
        assert 'closed' in tickets

    def test_get_itr_dashboard_data_issues_structure(self, db_session: Session):
        """测试问题统计结构"""
        result = get_itr_dashboard_data(db_session)
        issues = result['issues']

        assert 'total' in issues
        assert 'open' in issues
        assert 'processing' in issues
        assert 'resolved' in issues
        assert 'closed' in issues

    def test_get_itr_dashboard_data_acceptance_structure(self, db_session: Session):
        """测试验收统计结构"""
        result = get_itr_dashboard_data(db_session)
        acceptance = result['acceptance']

        assert 'total' in acceptance
        assert 'passed' in acceptance
        assert 'failed' in acceptance

    def test_get_itr_dashboard_data_sla_structure(self, db_session: Session):
        """测试SLA统计结构"""
        result = get_itr_dashboard_data(db_session)
        sla = result['sla']

        assert 'total' in sla
        assert 'response_on_time' in sla
        assert 'response_overdue' in sla
        assert 'resolve_on_time' in sla
        assert 'resolve_overdue' in sla
        assert 'response_rate' in sla
        assert 'resolve_rate' in sla

    def test_get_itr_dashboard_data_with_project_filter(self, db_session: Session):
        """测试按项目筛选"""
        result = get_itr_dashboard_data(db_session, project_id=1)
        assert 'tickets' in result
        assert isinstance(result['tickets']['total'], int)

    def test_get_itr_dashboard_data_with_date_filter(self, db_session: Session):
        """测试按日期筛选"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        result = get_itr_dashboard_data(
            db_session,
            start_date=start_date,
            end_date=end_date
        )
        assert 'tickets' in result
        assert isinstance(result['tickets']['total'], int)
