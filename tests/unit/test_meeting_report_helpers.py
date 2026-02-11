# -*- coding: utf-8 -*-
"""Tests for meeting_report_helpers.py"""
from unittest.mock import MagicMock, patch
from datetime import date

from app.services.meeting_report_helpers import (
    calculate_periods,
    calculate_meeting_statistics,
    calculate_action_item_statistics,
    calculate_completion_rate,
    calculate_change,
    collect_key_decisions,
    calculate_by_level_statistics,
    build_report_summary,
)


class TestCalculatePeriods:
    def test_normal_month(self):
        s, e, ps, pe = calculate_periods(2025, 6)
        assert s == date(2025, 6, 1)
        assert e == date(2025, 6, 30)
        assert ps == date(2025, 5, 1)
        assert pe == date(2025, 5, 31)

    def test_january_wraps(self):
        s, e, ps, pe = calculate_periods(2025, 1)
        assert ps == date(2024, 12, 1)
        assert pe == date(2024, 12, 31)

    def test_february(self):
        s, e, ps, pe = calculate_periods(2024, 2)
        assert e == date(2024, 2, 29)  # leap year


class TestCalculateMeetingStatistics:
    def test_basic(self):
        meetings = [
            MagicMock(status="COMPLETED"),
            MagicMock(status="COMPLETED"),
            MagicMock(status="PENDING"),
        ]
        total, completed = calculate_meeting_statistics(meetings)
        assert total == 3
        assert completed == 2

    def test_empty(self):
        total, completed = calculate_meeting_statistics([])
        assert total == 0
        assert completed == 0


class TestCalculateActionItemStatistics:
    def test_empty_ids(self):
        db = MagicMock()
        total, completed, overdue = calculate_action_item_statistics(db, [])
        assert total == 0

    def test_with_ids(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 10
        total, completed, overdue = calculate_action_item_statistics(db, [1, 2])
        assert total == 10


class TestCalculateCompletionRate:
    def test_normal(self):
        assert calculate_completion_rate(3, 10) == "30.0%"

    def test_zero_total(self):
        assert calculate_completion_rate(0, 0) == "0.0%"


class TestCalculateChange:
    def test_increase(self):
        result = calculate_change(10, 8)
        assert result['change'] == 2
        assert result['current'] == 10

    def test_from_zero(self):
        result = calculate_change(5, 0)
        assert result['change_rate'] == "+100.0%"

    def test_both_zero(self):
        result = calculate_change(0, 0)
        assert result['change'] == 0


class TestCollectKeyDecisions:
    def test_basic(self):
        m1 = MagicMock(key_decisions=["决策A", "决策B"])
        m2 = MagicMock(key_decisions=None)
        m3 = MagicMock(key_decisions=["决策C"])
        result = collect_key_decisions([m1, m2, m3])
        assert len(result) == 3


class TestCalculateByLevelStatistics:
    def test_basic(self):
        meetings = [
            MagicMock(rhythm_level="L1", status="COMPLETED"),
            MagicMock(rhythm_level="L1", status="PENDING"),
            MagicMock(rhythm_level="L2", status="COMPLETED"),
        ]
        result = calculate_by_level_statistics(meetings)
        assert result['L1']['total'] == 2
        assert result['L1']['completed'] == 1
        assert result['L2']['total'] == 1


class TestBuildReportSummary:
    def test_basic(self):
        result = build_report_summary(
            {'total': 10, 'completed': 8},
            {'total': 20, 'completed': 15, 'overdue': 3},
            75.0
        )
        assert result['total_meetings'] == 10
        assert result['completion_rate'] == "80.0%"
        assert result['action_completion_rate'] == "75.0%"
