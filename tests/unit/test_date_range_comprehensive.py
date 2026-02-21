# -*- coding: utf-8 -*-
"""
时间范围工具全面测试

测试 app/common/date_range.py 中的所有函数
"""
import pytest
from datetime import date, timedelta

from app.common.date_range import (
    get_month_range,
    get_last_month_range,
    get_month_range_by_ym,
    month_start,
    month_end,
    get_week_range,
)


class TestGetMonthRange:
    """测试获取月份范围函数"""

    def test_january(self):
        """测试1月"""
        target = date(2025, 1, 15)
        start, end = get_month_range(target)
        
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)
    
    def test_february_non_leap_year(self):
        """测试非闰年2月"""
        target = date(2025, 2, 15)
        start, end = get_month_range(target)
        
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)
    
    def test_february_leap_year(self):
        """测试闰年2月"""
        target = date(2024, 2, 15)
        start, end = get_month_range(target)
        
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)
    
    def test_december(self):
        """测试12月"""
        target = date(2025, 12, 15)
        start, end = get_month_range(target)
        
        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)
    
    def test_month_with_30_days(self):
        """测试30天的月份"""
        target = date(2025, 4, 15)
        start, end = get_month_range(target)
        
        assert start == date(2025, 4, 1)
        assert end == date(2025, 4, 30)
    
    def test_month_with_31_days(self):
        """测试31天的月份"""
        target = date(2025, 7, 15)
        start, end = get_month_range(target)
        
        assert start == date(2025, 7, 1)
        assert end == date(2025, 7, 31)
    
    def test_first_day_of_month(self):
        """测试月初"""
        target = date(2025, 3, 1)
        start, end = get_month_range(target)
        
        assert start == date(2025, 3, 1)
        assert end == date(2025, 3, 31)
    
    def test_last_day_of_month(self):
        """测试月末"""
        target = date(2025, 3, 31)
        start, end = get_month_range(target)
        
        assert start == date(2025, 3, 1)
        assert end == date(2025, 3, 31)


class TestGetLastMonthRange:
    """测试获取上月范围函数"""

    def test_january_returns_december_last_year(self):
        """测试1月返回去年12月"""
        target = date(2025, 1, 15)
        start, end = get_last_month_range(target)
        
        assert start == date(2024, 12, 1)
        assert end == date(2024, 12, 31)
    
    def test_march_returns_february(self):
        """测试3月返回2月"""
        target = date(2025, 3, 15)
        start, end = get_last_month_range(target)
        
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)
    
    def test_march_leap_year_returns_february_29(self):
        """测试闰年3月返回2月29"""
        target = date(2024, 3, 15)
        start, end = get_last_month_range(target)
        
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)
    
    def test_may_returns_april(self):
        """测试5月返回4月"""
        target = date(2025, 5, 15)
        start, end = get_last_month_range(target)
        
        assert start == date(2025, 4, 1)
        assert end == date(2025, 4, 30)
    
    def test_first_day_of_month(self):
        """测试月初"""
        target = date(2025, 6, 1)
        start, end = get_last_month_range(target)
        
        assert start == date(2025, 5, 1)
        assert end == date(2025, 5, 31)


class TestGetMonthRangeByYM:
    """测试通过年月获取范围函数"""

    def test_january_2025(self):
        """测试2025年1月"""
        start, end = get_month_range_by_ym(2025, 1)
        
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)
    
    def test_december_2025(self):
        """测试2025年12月"""
        start, end = get_month_range_by_ym(2025, 12)
        
        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)
    
    def test_february_non_leap(self):
        """测试非闰年2月"""
        start, end = get_month_range_by_ym(2025, 2)
        
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)
    
    def test_february_leap(self):
        """测试闰年2月"""
        start, end = get_month_range_by_ym(2024, 2)
        
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)
    
    def test_april_30_days(self):
        """测试4月30天"""
        start, end = get_month_range_by_ym(2025, 4)
        
        assert start == date(2025, 4, 1)
        assert end == date(2025, 4, 30)
    
    def test_july_31_days(self):
        """测试7月31天"""
        start, end = get_month_range_by_ym(2025, 7)
        
        assert start == date(2025, 7, 1)
        assert end == date(2025, 7, 31)


class TestMonthStart:
    """测试月初函数"""

    def test_middle_of_month(self):
        """测试月中"""
        result = month_start(date(2025, 6, 15))
        assert result == date(2025, 6, 1)
    
    def test_first_day_of_month(self):
        """测试月初"""
        result = month_start(date(2025, 6, 1))
        assert result == date(2025, 6, 1)
    
    def test_last_day_of_month(self):
        """测试月末"""
        result = month_start(date(2025, 6, 30))
        assert result == date(2025, 6, 1)
    
    def test_january(self):
        """测试1月"""
        result = month_start(date(2025, 1, 20))
        assert result == date(2025, 1, 1)
    
    def test_december(self):
        """测试12月"""
        result = month_start(date(2025, 12, 25))
        assert result == date(2025, 12, 1)


class TestMonthEnd:
    """测试月末函数"""

    def test_middle_of_month(self):
        """测试月中"""
        result = month_end(date(2025, 6, 15))
        assert result == date(2025, 6, 30)
    
    def test_first_day_of_month(self):
        """测试月初"""
        result = month_end(date(2025, 6, 1))
        assert result == date(2025, 6, 30)
    
    def test_last_day_of_month(self):
        """测试月末"""
        result = month_end(date(2025, 6, 30))
        assert result == date(2025, 6, 30)
    
    def test_january_31(self):
        """测试1月31天"""
        result = month_end(date(2025, 1, 15))
        assert result == date(2025, 1, 31)
    
    def test_february_non_leap(self):
        """测试非闰年2月28天"""
        result = month_end(date(2025, 2, 15))
        assert result == date(2025, 2, 28)
    
    def test_february_leap(self):
        """测试闰年2月29天"""
        result = month_end(date(2024, 2, 15))
        assert result == date(2024, 2, 29)
    
    def test_april_30(self):
        """测试4月30天"""
        result = month_end(date(2025, 4, 15))
        assert result == date(2025, 4, 30)


class TestGetWeekRange:
    """测试获取周范围函数"""

    def test_monday(self):
        """测试周一"""
        target = date(2025, 2, 17)  # 周一
        start, end = get_week_range(target)
        
        assert start == date(2025, 2, 17)
        assert end == date(2025, 2, 23)
    
    def test_tuesday(self):
        """测试周二"""
        target = date(2025, 2, 18)  # 周二
        start, end = get_week_range(target)
        
        assert start == date(2025, 2, 17)
        assert end == date(2025, 2, 23)
    
    def test_sunday(self):
        """测试周日"""
        target = date(2025, 2, 23)  # 周日
        start, end = get_week_range(target)
        
        assert start == date(2025, 2, 17)
        assert end == date(2025, 2, 23)
    
    def test_week_spanning_months(self):
        """测试跨月的周"""
        target = date(2025, 3, 3)  # 周一
        start, end = get_week_range(target)
        
        assert start == date(2025, 3, 3)
        assert end == date(2025, 3, 9)
    
    def test_week_spanning_years(self):
        """测试跨年的周"""
        target = date(2025, 1, 1)  # 周三
        start, end = get_week_range(target)
        
        # 周一是2024年12月30日
        assert start == date(2024, 12, 30)
        assert end == date(2025, 1, 5)


class TestIntegrationScenarios:
    """集成测试场景"""

    def test_financial_month_report(self):
        """测试财务月报场景"""
        report_date = date(2025, 3, 15)
        
        # 当月范围
        current_start, current_end = get_month_range(report_date)
        assert current_start == date(2025, 3, 1)
        assert current_end == date(2025, 3, 31)
        
        # 上月范围
        last_start, last_end = get_last_month_range(report_date)
        assert last_start == date(2025, 2, 1)
        assert last_end == date(2025, 2, 28)
    
    def test_weekly_schedule(self):
        """测试周度排班场景"""
        today = date(2025, 2, 19)  # 周三
        
        # 本周范围
        week_start, week_end = get_week_range(today)
        assert week_start == date(2025, 2, 17)  # 周一
        assert week_end == date(2025, 2, 23)  # 周日
        
        # 上周范围
        last_week = today - timedelta(days=7)
        last_week_start, last_week_end = get_week_range(last_week)
        assert last_week_start == date(2025, 2, 10)
        assert last_week_end == date(2025, 2, 16)
    
    def test_quarter_range(self):
        """测试季度范围场景"""
        # Q1: 1-3月
        q1_months = [get_month_range_by_ym(2025, m) for m in [1, 2, 3]]
        assert q1_months[0][0] == date(2025, 1, 1)
        assert q1_months[2][1] == date(2025, 3, 31)
        
        # Q2: 4-6月
        q2_months = [get_month_range_by_ym(2025, m) for m in [4, 5, 6]]
        assert q2_months[0][0] == date(2025, 4, 1)
        assert q2_months[2][1] == date(2025, 6, 30)
    
    def test_year_end_processing(self):
        """测试年末处理场景"""
        year_end = date(2025, 12, 31)
        
        # 12月范围
        dec_start, dec_end = get_month_range(year_end)
        assert dec_start == date(2025, 12, 1)
        assert dec_end == date(2025, 12, 31)
        
        # 上月（11月）范围
        nov_start, nov_end = get_last_month_range(year_end)
        assert nov_start == date(2025, 11, 1)
        assert nov_end == date(2025, 11, 30)


class TestEdgeCases:
    """边界情况测试"""

    def test_leap_year_detection(self):
        """测试闰年检测"""
        # 2024是闰年
        _, feb_2024 = get_month_range_by_ym(2024, 2)
        assert feb_2024 == date(2024, 2, 29)
        
        # 2025不是闰年
        _, feb_2025 = get_month_range_by_ym(2025, 2)
        assert feb_2025 == date(2025, 2, 28)
        
        # 2000是闰年（能被400整除）
        _, feb_2000 = get_month_range_by_ym(2000, 2)
        assert feb_2000 == date(2000, 2, 29)
        
        # 1900不是闰年（能被100整除但不能被400整除）
        _, feb_1900 = get_month_range_by_ym(1900, 2)
        assert feb_1900 == date(1900, 2, 28)
    
    def test_year_boundary(self):
        """测试年度边界"""
        # 1月1日
        jan1 = date(2025, 1, 1)
        start, end = get_month_range(jan1)
        assert start == date(2025, 1, 1)
        
        # 12月31日
        dec31 = date(2025, 12, 31)
        start, end = get_month_range(dec31)
        assert end == date(2025, 12, 31)
    
    def test_consistency_between_methods(self):
        """测试不同方法的一致性"""
        target = date(2025, 6, 15)
        
        # get_month_range 和 get_month_range_by_ym 应该返回相同结果
        range1 = get_month_range(target)
        range2 = get_month_range_by_ym(2025, 6)
        assert range1 == range2
        
        # month_start 和 get_month_range 的开始应该一致
        start1 = month_start(target)
        start2, _ = get_month_range(target)
        assert start1 == start2
        
        # month_end 和 get_month_range 的结束应该一致
        end1 = month_end(target)
        _, end2 = get_month_range(target)
        assert end1 == end2
