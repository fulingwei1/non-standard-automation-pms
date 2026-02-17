# -*- coding: utf-8 -*-
"""
ITR流程效率分析服务单元测试 (F组) - MagicMock方式

使用 MagicMock 模拟数据库，覆盖更多业务逻辑路径
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.itr_analytics_service import (
    analyze_resolution_time,
    analyze_satisfaction_trend,
    identify_bottlenecks,
    analyze_sla_performance,
)


@pytest.fixture
def db():
    return MagicMock()


# ============================================================
# analyze_resolution_time 测试
# ============================================================

class TestAnalyzeResolutionTimeMocked:

    def test_empty_returns_zero_stats(self, db):
        """测试无数据时返回空统计"""
        db.query.return_value.filter.return_value.all.return_value = []
        result = analyze_resolution_time(db)
        assert result["total_tickets"] == 0
        assert result["avg_resolution_hours"] == 0
        assert result["median_resolution_hours"] == 0
        assert result["min_resolution_hours"] == 0
        assert result["max_resolution_hours"] == 0
        assert result["by_problem_type"] == []
        assert result["by_urgency"] == []

    def test_single_ticket(self, db):
        """测试单个工单"""
        now = datetime(2025, 1, 15, 12, 0)
        reported = datetime(2025, 1, 15, 8, 0)  # 4 hours
        ticket = MagicMock(
            id=1, ticket_no="TK-001",
            problem_type="BUG", urgency="HIGH",
            reported_time=reported, resolved_time=now,
            status="CLOSED"
        )
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [ticket]
        db.query.return_value = mock_q

        result = analyze_resolution_time(db)
        assert result["total_tickets"] == 1
        assert result["avg_resolution_hours"] == 4.0
        assert result["min_resolution_hours"] == 4.0
        assert result["max_resolution_hours"] == 4.0

    def test_multiple_tickets_stats(self, db):
        """测试多个工单的统计"""
        base = datetime(2025, 1, 15, 0, 0)
        t1 = MagicMock(id=1, ticket_no="TK-001", problem_type="BUG", urgency="HIGH",
                       reported_time=base, resolved_time=base + timedelta(hours=4))
        t2 = MagicMock(id=2, ticket_no="TK-002", problem_type="BUG", urgency="LOW",
                       reported_time=base, resolved_time=base + timedelta(hours=8))
        t3 = MagicMock(id=3, ticket_no="TK-003", problem_type="FEATURE", urgency="HIGH",
                       reported_time=base, resolved_time=base + timedelta(hours=12))
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [t1, t2, t3]
        db.query.return_value = mock_q

        result = analyze_resolution_time(db)
        assert result["total_tickets"] == 3
        assert result["avg_resolution_hours"] == 8.0
        assert result["min_resolution_hours"] == 4.0
        assert result["max_resolution_hours"] == 12.0
        # by_problem_type should have BUG and FEATURE
        problem_types = {d["problem_type"] for d in result["by_problem_type"]}
        assert "BUG" in problem_types
        assert "FEATURE" in problem_types

    def test_with_date_filters(self, db):
        """测试日期过滤器"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        start = datetime(2025, 1, 1)
        end = datetime(2025, 1, 31)
        result = analyze_resolution_time(db, start_date=start, end_date=end)
        assert result["total_tickets"] == 0

    def test_with_project_filter(self, db):
        """测试项目过滤器"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        result = analyze_resolution_time(db, project_id=42)
        assert "total_tickets" in result

    def test_ticket_without_reported_time(self, db):
        """测试缺少报告时间的工单（不应计入统计）"""
        ticket = MagicMock(
            id=1, ticket_no="TK-001",
            problem_type="BUG", urgency="HIGH",
            reported_time=None, resolved_time=datetime(2025, 1, 15, 12, 0)
        )
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [ticket]
        db.query.return_value = mock_q

        result = analyze_resolution_time(db)
        assert result["total_tickets"] == 0


# ============================================================
# analyze_satisfaction_trend 测试
# ============================================================

class TestAnalyzeSatisfactionTrendMocked:

    def test_empty_returns_zero_stats(self, db):
        """测试无数据"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value.all.return_value = []
        db.query.return_value = mock_q

        result = analyze_satisfaction_trend(db)
        assert result["total_surveys"] == 0
        assert result["avg_score"] == 0

    def test_single_survey(self, db):
        """测试单个调查"""
        survey = MagicMock(
            overall_score=85.0,
            survey_date=datetime(2025, 1, 15),
            survey_type="MONTHLY",
            status="COMPLETED"
        )
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value.all.return_value = [survey]
        db.query.return_value = mock_q

        result = analyze_satisfaction_trend(db)
        assert result["total_surveys"] == 1
        assert result["avg_score"] == 85.0

    def test_multiple_surveys_monthly_trend(self, db):
        """测试多个调查的月度趋势"""
        s1 = MagicMock(overall_score=80.0, survey_date=datetime(2025, 1, 10), survey_type="QUARTERLY")
        s2 = MagicMock(overall_score=90.0, survey_date=datetime(2025, 1, 20), survey_type="QUARTERLY")
        s3 = MagicMock(overall_score=70.0, survey_date=datetime(2025, 2, 15), survey_type="MONTHLY")
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value.all.return_value = [s1, s2, s3]
        db.query.return_value = mock_q

        result = analyze_satisfaction_trend(db)
        assert result["total_surveys"] == 3
        assert abs(result["avg_score"] - 80.0) < 0.1
        # Should have 2 months in trend
        assert len(result["trend_by_month"]) == 2

    def test_with_date_filter(self, db):
        """测试日期过滤"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value.all.return_value = []
        db.query.return_value = mock_q

        result = analyze_satisfaction_trend(
            db,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31)
        )
        assert result["total_surveys"] == 0


# ============================================================
# identify_bottlenecks 测试
# ============================================================

class TestIdentifyBottlenecksMocked:

    def test_empty_returns_empty_bottlenecks(self, db):
        """测试无数据"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        result = identify_bottlenecks(db)
        assert result["bottlenecks"] == []
        assert result["total_analyzed"] == 0
        assert result["critical_bottlenecks"] == []

    def test_fast_response_low_severity(self, db):
        """测试快速响应（低严重度）"""
        now = datetime(2025, 1, 15, 12, 0)
        ticket = MagicMock(
            id=1, problem_type="BUG",
            reported_time=now - timedelta(hours=2),
            assigned_time=now - timedelta(hours=1),  # 1 hour to assign
            resolved_time=now,
            status="CLOSED",
            timeline=None
        )
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [ticket]
        db.query.return_value = mock_q

        result = identify_bottlenecks(db)
        assert result["total_analyzed"] == 1
        # 1 hour assignment, LOW severity
        bottleneck = next((b for b in result["bottlenecks"] if "PENDING" in b["stage"]), None)
        assert bottleneck is not None
        assert bottleneck["severity"] == "LOW"

    def test_slow_response_high_severity(self, db):
        """测试慢响应（高严重度）"""
        now = datetime(2025, 1, 15, 12, 0)
        ticket = MagicMock(
            id=1, problem_type="BUG",
            reported_time=now - timedelta(hours=30),
            assigned_time=now,  # 30 hours to assign -> HIGH
            resolved_time=now + timedelta(hours=1),
            status="IN_PROGRESS",
            timeline=None
        )
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [ticket]
        db.query.return_value = mock_q

        result = identify_bottlenecks(db)
        assert result["total_analyzed"] == 1
        pending_bottleneck = next((b for b in result["bottlenecks"] if "PENDING" in b["stage"]), None)
        assert pending_bottleneck is not None
        assert pending_bottleneck["severity"] == "HIGH"
        assert len(result["critical_bottlenecks"]) > 0

    def test_with_date_filter(self, db):
        """测试日期过滤"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        result = identify_bottlenecks(
            db,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31)
        )
        assert result["total_analyzed"] == 0


# ============================================================
# analyze_sla_performance 测试
# ============================================================

class TestAnalyzeSlaPerformanceMocked:

    def test_empty_returns_zero_rates(self, db):
        """测试无数据"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        result = analyze_sla_performance(db)
        assert result["total_monitors"] == 0
        assert result["response_rate"] == 0
        assert result["resolve_rate"] == 0

    def test_all_on_time(self, db):
        """测试全部准时"""
        m1 = MagicMock(response_status="ON_TIME", resolve_status="ON_TIME", policy_id=1)
        m1.policy = MagicMock(policy_name="Standard SLA")
        m2 = MagicMock(response_status="ON_TIME", resolve_status="ON_TIME", policy_id=1)
        m2.policy = MagicMock(policy_name="Standard SLA")
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [m1, m2]
        db.query.return_value = mock_q

        result = analyze_sla_performance(db)
        assert result["total_monitors"] == 2
        assert result["response_rate"] == 100.0
        assert result["resolve_rate"] == 100.0

    def test_mixed_performance(self, db):
        """测试混合达成"""
        m1 = MagicMock(response_status="ON_TIME", resolve_status="ON_TIME", policy_id=1)
        m1.policy = MagicMock(policy_name="Standard SLA")
        m2 = MagicMock(response_status="OVERDUE", resolve_status="OVERDUE", policy_id=1)
        m2.policy = MagicMock(policy_name="Standard SLA")
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [m1, m2]
        db.query.return_value = mock_q

        result = analyze_sla_performance(db)
        assert result["total_monitors"] == 2
        assert result["response_rate"] == 50.0
        assert result["resolve_rate"] == 50.0
        assert result["response_on_time"] == 1
        assert result["response_overdue"] == 1

    def test_with_policy_filter(self, db):
        """测试按策略过滤"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        result = analyze_sla_performance(db, policy_id=5)
        assert result["total_monitors"] == 0

    def test_by_policy_breakdown(self, db):
        """测试按策略分组统计"""
        m1 = MagicMock(response_status="ON_TIME", resolve_status="ON_TIME", policy_id=1)
        m1.policy = MagicMock(policy_name="Policy A")
        m2 = MagicMock(response_status="OVERDUE", resolve_status="ON_TIME", policy_id=2)
        m2.policy = MagicMock(policy_name="Policy B")
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [m1, m2]
        db.query.return_value = mock_q

        result = analyze_sla_performance(db)
        assert len(result["by_policy"]) == 2
        policy_ids = {p["policy_id"] for p in result["by_policy"]}
        assert 1 in policy_ids
        assert 2 in policy_ids
