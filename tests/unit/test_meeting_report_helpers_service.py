# -*- coding: utf-8 -*-
"""
会议报告辅助函数单元测试
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


class TestCalculatePeriods:
    """测试计算周期"""

    def test_january(self):
        """测试一月"""
        from app.services.meeting_report_helpers import calculate_periods

        start, end, prev_start, prev_end = calculate_periods(2025, 1)

        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)
        assert prev_start == date(2024, 12, 1)
        assert prev_end == date(2024, 12, 31)

    def test_june(self):
        """测试六月"""
        from app.services.meeting_report_helpers import calculate_periods

        start, end, prev_start, prev_end = calculate_periods(2025, 6)

        assert start == date(2025, 6, 1)
        assert end == date(2025, 6, 30)
        assert prev_start == date(2025, 5, 1)
        assert prev_end == date(2025, 5, 31)

    def test_february_leap_year(self):
        """测试闰年二月"""
        from app.services.meeting_report_helpers import calculate_periods

        start, end, prev_start, prev_end = calculate_periods(2024, 2)

        assert end == date(2024, 2, 29)


class TestCalculateMeetingStatistics:
    """测试计算会议统计"""

    def test_empty_meetings(self):
        """测试空会议列表"""
        from app.services.meeting_report_helpers import calculate_meeting_statistics

        total, completed = calculate_meeting_statistics([])

        assert total == 0
        assert completed == 0

    def test_with_meetings(self):
        """测试有会议"""
        from app.services.meeting_report_helpers import calculate_meeting_statistics

        m1 = MagicMock()
        m1.status = "COMPLETED"
        m2 = MagicMock()
        m2.status = "SCHEDULED"
        m3 = MagicMock()
        m3.status = "COMPLETED"

        total, completed = calculate_meeting_statistics([m1, m2, m3])

        assert total == 3
        assert completed == 2


class TestCalculateCompletionRate:
    """测试计算完成率"""

    def test_zero_total(self):
        """测试总数为零"""
        from app.services.meeting_report_helpers import calculate_completion_rate

        result = calculate_completion_rate(0, 0)

        assert result == "0.0%"

    def test_full_completion(self):
        """测试全部完成"""
        from app.services.meeting_report_helpers import calculate_completion_rate

        result = calculate_completion_rate(10, 10)

        assert result == "100.0%"

    def test_partial_completion(self):
        """测试部分完成"""
        from app.services.meeting_report_helpers import calculate_completion_rate

        result = calculate_completion_rate(7, 10)

        assert result == "70.0%"


class TestCalculateChange:
    """测试计算变化"""

    def test_increase(self):
        """测试增加"""
        from app.services.meeting_report_helpers import calculate_change

        result = calculate_change(15, 10)

        assert result['current'] == 15
        assert result['previous'] == 10
        assert result['change'] == 5
        assert result['change_abs'] == 5

    def test_decrease(self):
        """测试减少"""
        from app.services.meeting_report_helpers import calculate_change

        result = calculate_change(8, 10)

        assert result['change'] == -2
        assert result['change_abs'] == 2

    def test_zero_previous(self):
        """测试上期为零"""
        from app.services.meeting_report_helpers import calculate_change

        result = calculate_change(10, 0)

        assert result['change'] == 10


class TestCollectKeyDecisions:
    """测试收集关键决策"""

    def test_empty_meetings(self):
        """测试空会议列表"""
        from app.services.meeting_report_helpers import collect_key_decisions

        result = collect_key_decisions([])

        assert result == []

    def test_with_decisions(self):
        """测试有决策"""
        from app.services.meeting_report_helpers import collect_key_decisions

        m1 = MagicMock()
        m1.key_decisions = ["决策1", "决策2"]
        m2 = MagicMock()
        m2.key_decisions = ["决策3"]
        m3 = MagicMock()
        m3.key_decisions = None

        result = collect_key_decisions([m1, m2, m3])

        assert len(result) == 3
        assert "决策1" in result
        assert "决策3" in result


class TestCalculateByLevelStatistics:
    """测试按层级统计"""

    def test_empty_meetings(self):
        """测试空会议列表"""
        from app.services.meeting_report_helpers import calculate_by_level_statistics

        result = calculate_by_level_statistics([])

        assert result == {}

    def test_multiple_levels(self):
        """测试多层级"""
        from app.services.meeting_report_helpers import calculate_by_level_statistics

        m1 = MagicMock()
        m1.rhythm_level = "WEEKLY"
        m1.status = "COMPLETED"

        m2 = MagicMock()
        m2.rhythm_level = "WEEKLY"
        m2.status = "SCHEDULED"

        m3 = MagicMock()
        m3.rhythm_level = "MONTHLY"
        m3.status = "COMPLETED"

        result = calculate_by_level_statistics([m1, m2, m3])

        assert result["WEEKLY"]["total"] == 2
        assert result["WEEKLY"]["completed"] == 1
        assert result["MONTHLY"]["total"] == 1
        assert result["MONTHLY"]["completed"] == 1


class TestBuildReportSummary:
    """测试构建报告摘要"""

    def test_build_summary(self):
        """测试构建摘要"""
        from app.services.meeting_report_helpers import build_report_summary

        meeting_stats = {'total': 10, 'completed': 8}
        action_item_stats = {'total': 20, 'completed': 15, 'overdue': 2}
        completion_rate = 75.0

        result = build_report_summary(meeting_stats, action_item_stats, completion_rate)

        assert result['total_meetings'] == 10
        assert result['completed_meetings'] == 8
        assert result['completion_rate'] == "80.0%"
        assert result['total_action_items'] == 20

    def test_zero_meetings(self):
        """测试无会议"""
        from app.services.meeting_report_helpers import build_report_summary

        meeting_stats = {'total': 0, 'completed': 0}
        action_item_stats = {'total': 0, 'completed': 0, 'overdue': 0}

        result = build_report_summary(meeting_stats, action_item_stats, 0.0)

        assert result['completion_rate'] == "0%"


class TestQueryMeetings:
    """测试查询会议"""

    def test_no_meetings(self, db_session):
        """测试无会议"""
        from app.services.meeting_report_helpers import query_meetings

        result = query_meetings(
        db_session,
        date(2025, 1, 1),
        date(2025, 1, 31)
        )

        assert result == []


class TestCalculateActionItemStatistics:
    """测试计算行动项统计"""

    def test_no_meeting_ids(self, db_session):
        """测试无会议ID"""
        from app.services.meeting_report_helpers import calculate_action_item_statistics

        total, completed, overdue = calculate_action_item_statistics(db_session, [])

        assert total == 0
        assert completed == 0
        assert overdue == 0


class TestBuildComparisonData:
    """测试构建对比数据"""

    def test_build_comparison(self):
        """测试构建对比"""
        from app.services.meeting_report_helpers import build_comparison_data

        current_stats = {
        'total': 10,
        'completed': 8,
        'action_items_total': 20,
        'action_items_completed': 15
        }
        prev_stats = {
        'total': 8,
        'completed': 6,
        'action_items_total': 15,
        'action_items_completed': 10
        }

        result = build_comparison_data(
        2025, 2, 2025, 1,
        current_stats, prev_stats,
        80.0, 75.0
        )

        assert result['previous_period'] == "2025-01"
        assert result['current_period'] == "2025-02"
        assert 'meetings_comparison' in result


class TestCollectStrategicStructures:
    """测试收集战略结构"""

    def test_empty_meetings(self):
        """测试空会议"""
        from app.services.meeting_report_helpers import collect_strategic_structures

        result = collect_strategic_structures([])

        assert result == []

    def test_with_structure(self):
        """测试有结构"""
        from app.services.meeting_report_helpers import collect_strategic_structures

        m = MagicMock()
        m.id = 1
        m.meeting_name = "周会"
        m.meeting_date = date(2025, 1, 15)
        m.strategic_structure = {"key": "value"}

        result = collect_strategic_structures([m])

        assert len(result) == 1
        assert result[0]['meeting_id'] == 1


# pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()
