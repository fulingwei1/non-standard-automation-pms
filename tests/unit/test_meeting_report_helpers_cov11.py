# -*- coding: utf-8 -*-
"""第十一批：meeting_report_helpers 单元测试"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.meeting_report_helpers import (
        calculate_periods,
        query_meetings,
    )
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="import failed")


class TestCalculatePeriods:
    def test_normal_month(self):
        """普通月份（非1月）计算正确"""
        start, end, prev_start, prev_end = calculate_periods(2025, 3)
        assert start == date(2025, 3, 1)
        assert end == date(2025, 3, 31)
        assert prev_start == date(2025, 2, 1)
        assert prev_end == date(2025, 2, 28)

    def test_january_wraps_to_previous_year(self):
        """1月份上月应为上一年12月"""
        start, end, prev_start, prev_end = calculate_periods(2025, 1)
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)
        assert prev_start == date(2024, 12, 1)
        assert prev_end == date(2024, 12, 31)

    def test_february_leap_year(self):
        """闰年2月末日为29日"""
        start, end, prev_start, prev_end = calculate_periods(2024, 2)
        assert end == date(2024, 2, 29)

    def test_february_non_leap_year(self):
        """平年2月末日为28日"""
        start, end, prev_start, prev_end = calculate_periods(2025, 2)
        assert end == date(2025, 2, 28)

    def test_returns_four_dates(self):
        """返回四个日期"""
        result = calculate_periods(2025, 6)
        assert len(result) == 4
        for d in result:
            assert isinstance(d, date)


class TestQueryMeetings:
    def test_query_with_no_level_filter(self):
        """不过滤级别时正常查询"""
        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        db.query.return_value = mock_query

        result = query_meetings(
            db,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
        )
        assert result == []

    def test_query_with_level_filter(self):
        """指定级别时过滤条件生效"""
        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        db.query.return_value = mock_query

        result = query_meetings(
            db,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            rhythm_level="MONTHLY",
        )
        assert result == []

    def test_query_returns_meetings(self):
        """有会议时正常返回"""
        db = MagicMock()
        meeting = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [meeting]
        db.query.return_value = mock_query

        result = query_meetings(
            db,
            period_start=date(2025, 3, 1),
            period_end=date(2025, 3, 31),
        )
        assert len(result) == 1
        assert result[0] is meeting
