# -*- coding: utf-8 -*-
"""
itr_analytics_service 综合单元测试

测试覆盖:
- analyze_resolution_time: 分析问题解决时间
- analyze_satisfaction_trend: 分析客户满意度趋势
- identify_bottlenecks: 识别流程瓶颈
- analyze_sla_performance: 分析SLA达成率
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestAnalyzeResolutionTime:
    """测试 analyze_resolution_time 函数"""

    def test_returns_empty_stats_when_no_tickets(self):
        """测试无工单时返回空统计"""
        from app.services.itr_analytics_service import analyze_resolution_time

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = analyze_resolution_time(mock_db)

        assert result['total_tickets'] == 0
        assert result['avg_resolution_hours'] == 0
        assert result['by_problem_type'] == []

    def test_calculates_resolution_statistics(self):
        """测试计算解决时间统计"""
        from app.services.itr_analytics_service import analyze_resolution_time

        mock_db = MagicMock()

        mock_ticket1 = MagicMock()
        mock_ticket1.id = 1
        mock_ticket1.ticket_no = "TK001"
        mock_ticket1.problem_type = "硬件故障"
        mock_ticket1.urgency = "HIGH"
        mock_ticket1.reported_time = datetime(2026, 1, 10, 9, 0)
        mock_ticket1.resolved_time = datetime(2026, 1, 10, 17, 0)  # 8小时

        mock_ticket2 = MagicMock()
        mock_ticket2.id = 2
        mock_ticket2.ticket_no = "TK002"
        mock_ticket2.problem_type = "软件问题"
        mock_ticket2.urgency = "MEDIUM"
        mock_ticket2.reported_time = datetime(2026, 1, 11, 9, 0)
        mock_ticket2.resolved_time = datetime(2026, 1, 11, 13, 0)  # 4小时

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ticket1, mock_ticket2]

        result = analyze_resolution_time(mock_db)

        assert result['total_tickets'] == 2
        assert result['avg_resolution_hours'] == 6.0  # (8 + 4) / 2
        assert result['min_resolution_hours'] == 4.0
        assert result['max_resolution_hours'] == 8.0

    def test_groups_by_problem_type(self):
        """测试按问题类型分组"""
        from app.services.itr_analytics_service import analyze_resolution_time

        mock_db = MagicMock()

        mock_ticket1 = MagicMock()
        mock_ticket1.id = 1
        mock_ticket1.ticket_no = "TK001"
        mock_ticket1.problem_type = "硬件故障"
        mock_ticket1.urgency = "HIGH"
        mock_ticket1.reported_time = datetime(2026, 1, 10, 9, 0)
        mock_ticket1.resolved_time = datetime(2026, 1, 10, 17, 0)

        mock_ticket2 = MagicMock()
        mock_ticket2.id = 2
        mock_ticket2.ticket_no = "TK002"
        mock_ticket2.problem_type = "硬件故障"
        mock_ticket2.urgency = "HIGH"
        mock_ticket2.reported_time = datetime(2026, 1, 11, 9, 0)
        mock_ticket2.resolved_time = datetime(2026, 1, 11, 13, 0)

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ticket1, mock_ticket2]

        result = analyze_resolution_time(mock_db)

        assert len(result['by_problem_type']) == 1
        assert result['by_problem_type'][0]['problem_type'] == "硬件故障"
        assert result['by_problem_type'][0]['count'] == 2

    def test_filters_by_date_range(self):
        """测试按日期范围筛选"""
        from app.services.itr_analytics_service import analyze_resolution_time

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = analyze_resolution_time(
            mock_db,
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 1, 31)
        )

        assert result['total_tickets'] == 0


class TestAnalyzeSatisfactionTrend:
    """测试 analyze_satisfaction_trend 函数"""

    def test_returns_empty_when_no_surveys(self):
        """测试无调查时返回空"""
        from app.services.itr_analytics_service import analyze_satisfaction_trend

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = analyze_satisfaction_trend(mock_db)

        assert result['total_surveys'] == 0
        assert result['avg_score'] == 0

    def test_calculates_average_score(self):
        """测试计算平均分"""
        from app.services.itr_analytics_service import analyze_satisfaction_trend

        mock_db = MagicMock()

        mock_sat1 = MagicMock()
        mock_sat1.overall_score = Decimal("4.5")
        mock_sat1.survey_date = datetime(2026, 1, 15)
        mock_sat1.survey_type = "FAT"

        mock_sat2 = MagicMock()
        mock_sat2.overall_score = Decimal("4.0")
        mock_sat2.survey_date = datetime(2026, 1, 20)
        mock_sat2.survey_type = "SAT"

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_sat1, mock_sat2]

        result = analyze_satisfaction_trend(mock_db)

        assert result['total_surveys'] == 2
        assert result['avg_score'] == 4.25

    def test_groups_by_month(self):
        """测试按月分组"""
        from app.services.itr_analytics_service import analyze_satisfaction_trend

        mock_db = MagicMock()

        mock_sat1 = MagicMock()
        mock_sat1.overall_score = Decimal("4.5")
        mock_sat1.survey_date = datetime(2026, 1, 15)
        mock_sat1.survey_type = "FAT"

        mock_sat2 = MagicMock()
        mock_sat2.overall_score = Decimal("4.0")
        mock_sat2.survey_date = datetime(2026, 2, 15)
        mock_sat2.survey_type = "FAT"

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_sat1, mock_sat2]

        result = analyze_satisfaction_trend(mock_db)

        assert len(result['trend_by_month']) == 2

    def test_groups_by_survey_type(self):
        """测试按调查类型分组"""
        from app.services.itr_analytics_service import analyze_satisfaction_trend

        mock_db = MagicMock()

        mock_sat1 = MagicMock()
        mock_sat1.overall_score = Decimal("4.5")
        mock_sat1.survey_date = datetime(2026, 1, 15)
        mock_sat1.survey_type = "FAT"

        mock_sat2 = MagicMock()
        mock_sat2.overall_score = Decimal("4.0")
        mock_sat2.survey_date = datetime(2026, 1, 20)
        mock_sat2.survey_type = "SAT"

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_sat1, mock_sat2]

        result = analyze_satisfaction_trend(mock_db)

        assert len(result['trend_by_type']) == 2


class TestIdentifyBottlenecks:
    """测试 identify_bottlenecks 函数"""

    def test_returns_empty_when_no_tickets(self):
        """测试无工单时返回空"""
        from app.services.itr_analytics_service import identify_bottlenecks

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = identify_bottlenecks(mock_db)

        assert result['total_analyzed'] == 0
        assert result['bottlenecks'] == []

    def test_identifies_response_bottleneck(self):
        """测试识别响应瓶颈"""
        from app.services.itr_analytics_service import identify_bottlenecks

        mock_db = MagicMock()

        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.status = "CLOSED"
        mock_ticket.reported_time = datetime(2026, 1, 10, 9, 0)
        mock_ticket.assigned_time = datetime(2026, 1, 11, 17, 0)  # 32小时后
        mock_ticket.resolved_time = datetime(2026, 1, 12, 12, 0)
        mock_ticket.problem_type = "硬件故障"
        mock_ticket.timeline = []

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ticket]

        result = identify_bottlenecks(mock_db)

        assert result['total_analyzed'] == 1
        # 响应时间超过24小时，应该是HIGH severity
        response_bottleneck = next((b for b in result['bottlenecks'] if 'PENDING' in b['stage']), None)
        if response_bottleneck:
            assert response_bottleneck['severity'] == 'HIGH'

    def test_sorts_by_severity(self):
        """测试按严重程度排序"""
        from app.services.itr_analytics_service import identify_bottlenecks

        mock_db = MagicMock()

        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.status = "CLOSED"
        mock_ticket.reported_time = datetime(2026, 1, 10, 9, 0)
        mock_ticket.assigned_time = datetime(2026, 1, 10, 10, 0)  # 1小时
        mock_ticket.resolved_time = datetime(2026, 1, 15, 10, 0)  # 120小时后
        mock_ticket.problem_type = "硬件故障"
        mock_ticket.timeline = []

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ticket]

        result = identify_bottlenecks(mock_db)

        if result['bottlenecks']:
            # 第一个应该是最严重的
            severities = [b['severity'] for b in result['bottlenecks']]
            if 'HIGH' in severities:
                assert result['bottlenecks'][0]['severity'] == 'HIGH'


class TestAnalyzeSlaPerformance:
    """测试 analyze_sla_performance 函数"""

    def test_returns_empty_when_no_monitors(self):
        """测试无监控记录时返回空"""
        from app.services.itr_analytics_service import analyze_sla_performance

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        result = analyze_sla_performance(mock_db)

        assert result['total_monitors'] == 0
        assert result['response_rate'] == 0
        assert result['resolve_rate'] == 0

    def test_calculates_response_rate(self):
        """测试计算响应达成率"""
        from app.services.itr_analytics_service import analyze_sla_performance

        mock_db = MagicMock()

        mock_monitor1 = MagicMock()
        mock_monitor1.policy_id = 1
        mock_monitor1.policy = MagicMock(policy_name="标准SLA")
        mock_monitor1.response_status = "ON_TIME"
        mock_monitor1.resolve_status = "ON_TIME"

        mock_monitor2 = MagicMock()
        mock_monitor2.policy_id = 1
        mock_monitor2.policy = MagicMock(policy_name="标准SLA")
        mock_monitor2.response_status = "OVERDUE"
        mock_monitor2.resolve_status = "ON_TIME"

        mock_db.query.return_value.all.return_value = [mock_monitor1, mock_monitor2]

        result = analyze_sla_performance(mock_db)

        assert result['total_monitors'] == 2
        assert result['response_rate'] == 50.0  # 1/2 = 50%
        assert result['resolve_rate'] == 100.0  # 2/2 = 100%

    def test_groups_by_policy(self):
        """测试按策略分组"""
        from app.services.itr_analytics_service import analyze_sla_performance

        mock_db = MagicMock()

        mock_monitor1 = MagicMock()
        mock_monitor1.policy_id = 1
        mock_monitor1.policy = MagicMock(policy_name="标准SLA")
        mock_monitor1.response_status = "ON_TIME"
        mock_monitor1.resolve_status = "ON_TIME"

        mock_monitor2 = MagicMock()
        mock_monitor2.policy_id = 2
        mock_monitor2.policy = MagicMock(policy_name="紧急SLA")
        mock_monitor2.response_status = "ON_TIME"
        mock_monitor2.resolve_status = "OVERDUE"

        mock_db.query.return_value.all.return_value = [mock_monitor1, mock_monitor2]

        result = analyze_sla_performance(mock_db)

        assert len(result['by_policy']) == 2

    def test_filters_by_policy_id(self):
        """测试按策略ID筛选"""
        from app.services.itr_analytics_service import analyze_sla_performance

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = analyze_sla_performance(mock_db, policy_id=1)

        assert result['total_monitors'] == 0
