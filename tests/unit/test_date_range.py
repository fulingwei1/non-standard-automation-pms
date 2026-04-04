# -*- coding: utf-8 -*-
"""通用时间范围工具单元测试"""
from datetime import date, timedelta

import pytest

from app.common.date_range import (
    get_last_month_range,
    get_month_range,
    get_month_range_by_ym,
    get_week_range,
    month_end,
    month_start,
)


class TestDateRange:
    def test_get_month_range_january(self):
        """测试1月"""
        start, end = get_month_range(date(2025, 1, 15))
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)

    def test_get_month_range_december(self):
        """测试12月"""
        start, end = get_month_range(date(2025, 12, 10))
        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)

    def test_get_month_range_february_non_leap(self):
        """测试非闰年2月"""
        start, end = get_month_range(date(2025, 2, 15))
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)

    def test_get_month_range_february_leap(self):
        """测试闰年2月"""
        start, end = get_month_range(date(2024, 2, 15))
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)

    def test_get_month_range_mid_year(self):
        """测试年中月份"""
        start, end = get_month_range(date(2025, 6, 20))
        assert start == date(2025, 6, 1)
        assert end == date(2025, 6, 30)

    def test_get_last_month_range(self):
        """测试获取上一月范围"""
        start, end = get_last_month_range(date(2025, 3, 15))
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)

    def test_get_last_month_range_january(self):
        """测试1月的上一月（去年12月）"""
        start, end = get_last_month_range(date(2025, 1, 15))
        assert start == date(2024, 12, 1)
        assert end == date(2024, 12, 31)

    def test_get_last_month_range_december(self):
        """测试12月的上一月"""
        start, end = get_last_month_range(date(2025, 12, 15))
        assert start == date(2025, 11, 1)
        assert end == date(2025, 11, 30)

    def test_get_month_range_by_ym(self):
        """测试根据年月获取月份范围"""
        start, end = get_month_range_by_ym(2025, 5)
        assert start == date(2025, 5, 1)
        assert end == date(2025, 5, 31)

    def test_get_month_range_by_ym_december(self):
        """测试12月"""
        start, end = get_month_range_by_ym(2025, 12)
        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)

    def test_get_month_range_by_ym_february_leap(self):
        """测试闰年2月"""
        start, end = get_month_range_by_ym(2024, 2)
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)

    def test_month_start(self):
        """测试获取月初"""
        assert month_start(date(2025, 3, 15)) == date(2025, 3, 1)
        assert month_start(date(2025, 1, 1)) == date(2025, 1, 1)
        assert month_start(date(2025, 12, 31)) == date(2025, 12, 1)

    def test_month_end(self):
        """测试获取月末"""
        assert month_end(date(2025, 3, 15)) == date(2025, 3, 31)
        assert month_end(date(2025, 1, 1)) == date(2025, 1, 31)
        assert month_end(date(2025, 2, 15)) == date(2025, 2, 28)
        assert month_end(date(2024, 2, 15)) == date(2024, 2, 29)  # 闰年

    def test_get_week_range_monday(self):
        """测试周一所在周"""
        start, end = get_week_range(date(2025, 1, 6))  # 周一
        assert start == date(2025, 1, 6)
        assert end == date(2025, 1, 12)

    def test_get_week_range_mid_week(self):
        """测试周中日期"""
        start, end = get_week_range(date(2025, 1, 8))  # 周三
        assert start == date(2025, 1, 6)
        assert end == date(2025, 1, 12)

    def test_get_week_range_sunday(self):
        """测试周日"""
        start, end = get_week_range(date(2025, 1, 12))  # 周日
        assert start == date(2025, 1, 6)
        assert end == date(2025, 1, 12)

    def test_get_week_range_year_boundary(self):
        """测试跨年的周"""
        start, end = get_week_range(date(2025, 1, 1))  # 周三
        assert start == date(2024, 12, 30)
        assert end == date(2025, 1, 5)