# -*- coding: utf-8 -*-
"""
ITR流程效率分析服务单元测试

测试覆盖:
- 问题解决时间分析
- 客户满意度趋势分析
- 流程瓶颈识别
- SLA达成率分析
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.services.itr_analytics_service import (
    analyze_resolution_time,
    analyze_satisfaction_trend,
    identify_bottlenecks,
    analyze_sla_performance,
)


class TestAnalyzeResolutionTime:
    """问题解决时间分析测试"""

    def test_analyze_resolution_time_empty(self, db_session: Session):
        """测试无数据时的返回结构"""
        result = analyze_resolution_time(db_session)

        assert 'total_tickets' in result
        assert 'avg_resolution_hours' in result
        assert 'median_resolution_hours' in result
        assert 'min_resolution_hours' in result
        assert 'max_resolution_hours' in result
        assert 'by_problem_type' in result
        assert 'by_urgency' in result

    def test_analyze_resolution_time_with_project_filter(self, db_session: Session):
        """测试按项目筛选"""
        result = analyze_resolution_time(db_session, project_id=1)
        assert isinstance(result['total_tickets'], int)

    def test_analyze_resolution_time_with_date_filter(self, db_session: Session):
        """测试按日期筛选"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        result = analyze_resolution_time(
        db_session,
        start_date=start_date,
        end_date=end_date
        )
        assert isinstance(result['total_tickets'], int)


class TestAnalyzeSatisfactionTrend:
    """客户满意度趋势分析测试"""

    def test_analyze_satisfaction_trend_empty(self, db_session: Session):
        """测试无数据时的返回结构"""
        result = analyze_satisfaction_trend(db_session)

        assert 'total_surveys' in result
        assert 'avg_score' in result
        assert 'trend_by_month' in result
        assert 'trend_by_type' in result

    def test_analyze_satisfaction_trend_with_project_filter(self, db_session: Session):
        """测试按项目筛选"""
        result = analyze_satisfaction_trend(db_session, project_id=1)
        assert isinstance(result['total_surveys'], int)

    def test_analyze_satisfaction_trend_with_date_filter(self, db_session: Session):
        """测试按日期筛选"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        result = analyze_satisfaction_trend(
        db_session,
        start_date=start_date,
        end_date=end_date
        )
        assert isinstance(result['total_surveys'], int)


class TestIdentifyBottlenecks:
    """流程瓶颈识别测试"""

    def test_identify_bottlenecks_empty(self, db_session: Session):
        """测试无数据时的返回结构"""
        result = identify_bottlenecks(db_session)

        assert 'bottlenecks' in result
        assert 'total_analyzed' in result
        assert 'critical_bottlenecks' in result
        assert isinstance(result['bottlenecks'], list)
        assert isinstance(result['critical_bottlenecks'], list)

    def test_identify_bottlenecks_with_date_filter(self, db_session: Session):
        """测试按日期筛选"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        result = identify_bottlenecks(
        db_session,
        start_date=start_date,
        end_date=end_date
        )
        assert isinstance(result['total_analyzed'], int)


class TestAnalyzeSlaPerformance:
    """SLA达成率分析测试"""

    def test_analyze_sla_performance_empty(self, db_session: Session):
        """测试无数据时的返回结构"""
        result = analyze_sla_performance(db_session)

        assert 'total_monitors' in result
        assert 'response_rate' in result
        assert 'resolve_rate' in result
        assert 'by_policy' in result

    def test_analyze_sla_performance_with_policy_filter(self, db_session: Session):
        """测试按策略筛选"""
        result = analyze_sla_performance(db_session, policy_id=1)
        assert isinstance(result['total_monitors'], int)

    def test_analyze_sla_performance_with_date_filter(self, db_session: Session):
        """测试按日期筛选"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        result = analyze_sla_performance(
        db_session,
        start_date=start_date,
        end_date=end_date
        )
        assert isinstance(result['total_monitors'], int)

    def test_analyze_sla_performance_zero_division_handling(self, db_session: Session):
        """测试零除处理"""
        # 使用不存在的策略ID确保没有数据
        result = analyze_sla_performance(db_session, policy_id=99999)

        # 应该处理零除情况
        assert result['response_rate'] == 0
        assert result['resolve_rate'] == 0
