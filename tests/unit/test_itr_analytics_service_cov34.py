# -*- coding: utf-8 -*-
"""ITR流程效率分析服务单元测试 - 第三十四批"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

pytest.importorskip("app.services.itr_analytics_service")

try:
    from app.services.itr_analytics_service import analyze_resolution_time
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    analyze_resolution_time = None


def make_ticket(ticket_id, ticket_no, problem_type, urgency,
                reported_offset_h, resolved_offset_h):
    """创建 mock 工单"""
    now = datetime.now()
    ticket = MagicMock()
    ticket.id = ticket_id
    ticket.ticket_no = ticket_no
    ticket.problem_type = problem_type
    ticket.urgency = urgency
    ticket.status = "CLOSED"
    ticket.reported_time = now - timedelta(hours=reported_offset_h)
    ticket.resolved_time = now - timedelta(hours=resolved_offset_h)
    return ticket


class TestAnalyzeResolutionTime:
    def test_empty_results(self):
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        result = analyze_resolution_time(db)
        assert result["total_tickets"] == 0
        assert result["avg_resolution_hours"] == 0

    def test_single_ticket_stats(self):
        db = MagicMock()
        ticket = make_ticket(1, "T001", "hardware", "HIGH",
                             reported_offset_h=24, resolved_offset_h=0)

        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [ticket]
        db.query.return_value = mock_q

        result = analyze_resolution_time(db)
        assert result["total_tickets"] == 1
        assert result["avg_resolution_hours"] > 0

    def test_by_problem_type_grouping(self):
        db = MagicMock()
        t1 = make_ticket(1, "T001", "hardware", "HIGH", 10, 0)
        t2 = make_ticket(2, "T002", "software", "LOW", 5, 0)

        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [t1, t2]
        db.query.return_value = mock_q

        result = analyze_resolution_time(db)
        assert "by_problem_type" in result
        problem_types = [x["problem_type"] for x in result["by_problem_type"]]
        assert "hardware" in problem_types
        assert "software" in problem_types

    def test_by_urgency_grouping(self):
        db = MagicMock()
        t1 = make_ticket(1, "T001", "hardware", "HIGH", 10, 0)
        t2 = make_ticket(2, "T002", "software", "LOW", 5, 0)

        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [t1, t2]
        db.query.return_value = mock_q

        result = analyze_resolution_time(db)
        assert "by_urgency" in result
        urgencies = [x["urgency"] for x in result["by_urgency"]]
        assert "HIGH" in urgencies

    def test_with_date_filters(self):
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        result = analyze_resolution_time(db, start_date=start, end_date=end)
        assert result["total_tickets"] == 0

    def test_ticket_with_no_reported_time(self):
        """reported_time 缺失时应跳过该工单"""
        db = MagicMock()
        ticket = MagicMock()
        ticket.id = 99
        ticket.ticket_no = "T099"
        ticket.problem_type = "misc"
        ticket.urgency = "MED"
        ticket.status = "CLOSED"
        ticket.reported_time = None
        ticket.resolved_time = datetime.now()

        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [ticket]
        db.query.return_value = mock_q

        result = analyze_resolution_time(db)
        # No valid resolution times, should return zeros
        assert result["total_tickets"] == 0

    def test_min_max_computed(self):
        db = MagicMock()
        t1 = make_ticket(1, "T001", "type_a", "HIGH", 20, 0)
        t2 = make_ticket(2, "T002", "type_a", "LOW", 10, 0)

        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [t1, t2]
        db.query.return_value = mock_q

        result = analyze_resolution_time(db)
        assert result["max_resolution_hours"] >= result["min_resolution_hours"]
