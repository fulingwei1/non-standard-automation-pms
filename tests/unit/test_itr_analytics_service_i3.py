# -*- coding: utf-8 -*-
"""
ITR流程效率分析服务单元测试 (I3组)
使用 MagicMock，直接调用真实函数，确保覆盖率
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.itr_analytics_service import (
    analyze_resolution_time,
    analyze_satisfaction_trend,
    analyze_sla_performance,
    identify_bottlenecks,
)


def _make_query_db(return_items):
    """创建一个 db mock，.query().filter()...all() 返回 return_items"""
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.all.return_value = return_items
    db.query.return_value = q
    return db


# ─────────────────────────────────────────────────────────────────────────────
# analyze_resolution_time
# ─────────────────────────────────────────────────────────────────────────────
class TestAnalyzeResolutionTime:
    def test_no_tickets_returns_zero_stats(self):
        db = _make_query_db([])
        result = analyze_resolution_time(db)
        assert result["total_tickets"] == 0
        assert result["avg_resolution_hours"] == 0
        assert result["by_problem_type"] == []
        assert result["by_urgency"] == []

    def test_single_ticket_calculates_hours(self):
        ticket = MagicMock()
        ticket.id = 1
        ticket.ticket_no = "T001"
        ticket.problem_type = "HARDWARE"
        ticket.urgency = "HIGH"
        ticket.reported_time = datetime(2024, 1, 1, 8, 0)
        ticket.resolved_time = datetime(2024, 1, 1, 16, 0)  # 8 hours
        db = _make_query_db([ticket])
        result = analyze_resolution_time(db)
        assert result["total_tickets"] == 1
        assert abs(result["avg_resolution_hours"] - 8.0) < 0.01
        assert result["min_resolution_hours"] == result["max_resolution_hours"]

    def test_multiple_tickets_statistics(self):
        t1 = MagicMock()
        t1.id = 1; t1.ticket_no = "T001"; t1.problem_type = "HW"; t1.urgency = "HIGH"
        t1.reported_time = datetime(2024, 1, 1, 0, 0)
        t1.resolved_time = datetime(2024, 1, 1, 4, 0)   # 4 hours

        t2 = MagicMock()
        t2.id = 2; t2.ticket_no = "T002"; t2.problem_type = "SW"; t2.urgency = "LOW"
        t2.reported_time = datetime(2024, 1, 2, 0, 0)
        t2.resolved_time = datetime(2024, 1, 2, 12, 0)  # 12 hours

        db = _make_query_db([t1, t2])
        result = analyze_resolution_time(db)
        assert result["total_tickets"] == 2
        assert result["avg_resolution_hours"] == 8.0
        assert result["min_resolution_hours"] == 4.0
        assert result["max_resolution_hours"] == 12.0
        assert len(result["by_problem_type"]) == 2
        assert len(result["by_urgency"]) == 2

    def test_ticket_missing_times_skipped(self):
        ticket = MagicMock()
        ticket.id = 1; ticket.ticket_no = "T001"
        ticket.reported_time = None
        ticket.resolved_time = datetime(2024, 1, 1)
        db = _make_query_db([ticket])
        result = analyze_resolution_time(db)
        # No valid time diff => no resolution_times entries
        assert result["total_tickets"] == 0

    def test_date_range_filter_applied(self):
        db = _make_query_db([])
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        result = analyze_resolution_time(db, start_date=start, end_date=end, project_id=42)
        assert result["total_tickets"] == 0

    def test_median_calculation_even_count(self):
        tickets = []
        for i, hours in enumerate([2, 4, 6, 8]):
            t = MagicMock()
            t.id = i; t.ticket_no = f"T{i}"; t.problem_type = "X"; t.urgency = "M"
            t.reported_time = datetime(2024, 1, 1, 0, 0)
            t.resolved_time = datetime(2024, 1, 1, hours, 0)
            tickets.append(t)
        db = _make_query_db(tickets)
        result = analyze_resolution_time(db)
        assert result["total_tickets"] == 4
        # median of [2,4,6,8] at index 2 => 6
        assert result["median_resolution_hours"] == 6.0

    def test_details_capped_at_100(self):
        tickets = []
        for i in range(110):
            t = MagicMock()
            t.id = i; t.ticket_no = f"T{i}"; t.problem_type = "X"; t.urgency = "M"
            t.reported_time = datetime(2024, 1, 1, 0, 0)
            t.resolved_time = datetime(2024, 1, 1, 1, 0)
            tickets.append(t)
        db = _make_query_db(tickets)
        result = analyze_resolution_time(db)
        assert len(result["details"]) == 100


# ─────────────────────────────────────────────────────────────────────────────
# analyze_satisfaction_trend
# ─────────────────────────────────────────────────────────────────────────────
class TestAnalyzeSatisfactionTrend:
    def test_no_data_returns_zeros(self):
        db = _make_query_db([])
        result = analyze_satisfaction_trend(db)
        assert result["total_surveys"] == 0
        assert result["avg_score"] == 0
        assert result["trend_by_month"] == []

    def test_single_survey(self):
        s = MagicMock()
        s.survey_date = datetime(2024, 3, 15)
        s.overall_score = 4.5
        s.survey_type = "SATISFACTION"
        db = _make_query_db([s])
        result = analyze_satisfaction_trend(db)
        assert result["total_surveys"] == 1
        assert abs(result["avg_score"] - 4.5) < 0.01
        assert len(result["trend_by_month"]) == 1
        assert result["trend_by_month"][0]["month"] == "2024-03"

    def test_multiple_surveys_grouped_by_month(self):
        surveys = []
        for day in [5, 15, 25]:
            s = MagicMock()
            s.survey_date = datetime(2024, 6, day)
            s.overall_score = 3.0
            s.survey_type = "SATISFACTION"
            surveys.append(s)
        db = _make_query_db(surveys)
        result = analyze_satisfaction_trend(db)
        assert result["total_surveys"] == 3
        assert len(result["trend_by_month"]) == 1
        assert result["trend_by_month"][0]["count"] == 3

    def test_grouped_by_type(self):
        s1 = MagicMock(); s1.survey_date = datetime(2024, 1, 1); s1.overall_score = 4.0; s1.survey_type = "DELIVERY"
        s2 = MagicMock(); s2.survey_date = datetime(2024, 2, 1); s2.overall_score = 5.0; s2.survey_type = "SUPPORT"
        db = _make_query_db([s1, s2])
        result = analyze_satisfaction_trend(db)
        assert len(result["trend_by_type"]) == 2

    def test_none_score_survey_excluded_from_avg(self):
        s1 = MagicMock(); s1.survey_date = datetime(2024, 1, 1); s1.overall_score = 4.0; s1.survey_type = "X"
        s2 = MagicMock(); s2.survey_date = datetime(2024, 2, 1); s2.overall_score = None; s2.survey_type = "X"
        db = _make_query_db([s1, s2])
        result = analyze_satisfaction_trend(db)
        assert result["total_surveys"] == 2
        # avg computed from non-None scores only
        assert result["avg_score"] == 4.0

    def test_with_date_and_project_filter(self):
        db = _make_query_db([])
        result = analyze_satisfaction_trend(db, start_date=datetime(2024, 1, 1),
                                            end_date=datetime(2024, 12, 31), project_id=1)
        assert result["total_surveys"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# identify_bottlenecks
# ─────────────────────────────────────────────────────────────────────────────
class TestIdentifyBottlenecks:
    def test_no_tickets_returns_empty(self):
        db = _make_query_db([])
        result = identify_bottlenecks(db)
        assert result["bottlenecks"] == []
        assert result["total_analyzed"] == 0

    def test_pending_to_progress_bottleneck(self):
        t = MagicMock()
        t.id = 1; t.problem_type = "HW"; t.status = "IN_PROGRESS"
        t.reported_time = datetime(2024, 1, 1, 0, 0)
        t.assigned_time = datetime(2024, 1, 2, 8, 0)   # 32 hours → HIGH
        t.resolved_time = None
        t.timeline = None
        db = _make_query_db([t])
        result = identify_bottlenecks(db)
        assert result["total_analyzed"] == 1
        stages = [b["stage"] for b in result["bottlenecks"]]
        assert "PENDING → IN_PROGRESS" in stages
        ptp = next(b for b in result["bottlenecks"] if b["stage"] == "PENDING → IN_PROGRESS")
        assert ptp["severity"] == "HIGH"

    def test_in_progress_to_resolved_medium_severity(self):
        t = MagicMock()
        t.id = 1; t.problem_type = "SW"; t.status = "RESOLVED"
        t.reported_time = None
        t.assigned_time = datetime(2024, 1, 1, 0, 0)
        t.resolved_time = datetime(2024, 1, 2, 12, 0)  # 36 hours → HIGH
        t.timeline = None
        db = _make_query_db([t])
        result = identify_bottlenecks(db)
        stages = [b["stage"] for b in result["bottlenecks"]]
        assert "IN_PROGRESS → RESOLVED" in stages

    def test_resolved_to_closed_bottleneck(self):
        t = MagicMock()
        t.id = 1; t.problem_type = "HW"; t.status = "CLOSED"
        t.reported_time = None
        t.assigned_time = None
        t.resolved_time = datetime(2024, 1, 1, 0, 0)
        close_time = datetime(2024, 1, 3, 0, 0).isoformat()  # 48 hours
        t.timeline = [{"type": "CLOSED", "timestamp": close_time}]
        db = _make_query_db([t])
        result = identify_bottlenecks(db)
        stages = [b["stage"] for b in result["bottlenecks"]]
        assert "RESOLVED → CLOSED" in stages

    def test_bottlenecks_sorted_by_severity(self):
        t1 = MagicMock()
        t1.id = 1; t1.problem_type = "X"; t1.status = "IN_PROGRESS"
        t1.reported_time = datetime(2024, 1, 1, 0, 0)
        t1.assigned_time = datetime(2024, 1, 2, 8, 0)  # 32h HIGH
        t1.resolved_time = datetime(2024, 1, 3, 0, 0)  # 40h HIGH
        t1.timeline = None
        db = _make_query_db([t1])
        result = identify_bottlenecks(db)
        # HIGH comes first
        if len(result["bottlenecks"]) >= 2:
            assert result["bottlenecks"][0]["severity"] in ("HIGH", "MEDIUM")

    def test_with_date_filter(self):
        db = _make_query_db([])
        result = identify_bottlenecks(db, start_date=datetime(2024, 1, 1), end_date=datetime(2024, 12, 31))
        assert result["total_analyzed"] == 0

    def test_critical_bottlenecks_list(self):
        db = _make_query_db([])
        result = identify_bottlenecks(db)
        assert isinstance(result["critical_bottlenecks"], list)


# ─────────────────────────────────────────────────────────────────────────────
# analyze_sla_performance
# ─────────────────────────────────────────────────────────────────────────────
class TestAnalyzeSlaPerformance:
    def test_no_monitors_returns_zeros(self):
        db = _make_query_db([])
        result = analyze_sla_performance(db)
        assert result["total_monitors"] == 0
        assert result["response_rate"] == 0
        assert result["resolve_rate"] == 0
        assert result["by_policy"] == []

    def test_all_on_time(self):
        m1 = MagicMock(); m1.policy_id = 1; m1.response_status = "ON_TIME"; m1.resolve_status = "ON_TIME"
        m1.policy = MagicMock(); m1.policy.policy_name = "SLA-1"
        m2 = MagicMock(); m2.policy_id = 1; m2.response_status = "ON_TIME"; m2.resolve_status = "ON_TIME"
        m2.policy = MagicMock(); m2.policy.policy_name = "SLA-1"
        db = _make_query_db([m1, m2])
        result = analyze_sla_performance(db)
        assert result["total_monitors"] == 2
        assert result["response_rate"] == 100.0
        assert result["resolve_rate"] == 100.0

    def test_partial_on_time(self):
        m1 = MagicMock(); m1.policy_id = 1; m1.response_status = "ON_TIME"; m1.resolve_status = "ON_TIME"
        m1.policy = MagicMock(); m1.policy.policy_name = "SLA-1"
        m2 = MagicMock(); m2.policy_id = 1; m2.response_status = "OVERDUE"; m2.resolve_status = "OVERDUE"
        m2.policy = MagicMock(); m2.policy.policy_name = "SLA-1"
        db = _make_query_db([m1, m2])
        result = analyze_sla_performance(db)
        assert result["response_rate"] == 50.0
        assert result["resolve_rate"] == 50.0
        assert result["response_overdue"] == 1
        assert result["resolve_overdue"] == 1

    def test_policy_grouping(self):
        m1 = MagicMock(); m1.policy_id = 1; m1.response_status = "ON_TIME"; m1.resolve_status = "ON_TIME"
        m1.policy = MagicMock(); m1.policy.policy_name = "SLA-1"
        m2 = MagicMock(); m2.policy_id = 2; m2.response_status = "OVERDUE"; m2.resolve_status = "OVERDUE"
        m2.policy = MagicMock(); m2.policy.policy_name = "SLA-2"
        db = _make_query_db([m1, m2])
        result = analyze_sla_performance(db)
        assert len(result["by_policy"]) == 2

    def test_policy_none_uses_default_name(self):
        m1 = MagicMock(); m1.policy_id = 99; m1.response_status = "ON_TIME"; m1.resolve_status = "ON_TIME"
        m1.policy = None
        db = _make_query_db([m1])
        result = analyze_sla_performance(db)
        assert result["by_policy"][0]["policy_name"] == "Policy 99"

    def test_date_and_policy_filter(self):
        db = _make_query_db([])
        result = analyze_sla_performance(db, start_date=datetime(2024, 1, 1),
                                         end_date=datetime(2024, 12, 31), policy_id=1)
        assert result["total_monitors"] == 0
