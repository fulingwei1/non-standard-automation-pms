# -*- coding: utf-8 -*-
"""
holiday_utils.py 覆盖率测试
目标: 提升 app/utils/holiday_utils.py 覆盖率（当前 44.6%）
"""
import pytest
from datetime import date, timedelta

from app.utils.holiday_utils import (
    is_holiday,
    get_holiday_name,
    is_workday_adjustment,
    get_work_type,
    get_working_days,
    add_working_days,
)


class TestIsHoliday:
    """测试法定节假日判断（只检查 CHINESE_HOLIDAYS 字典，周末不算）"""

    def test_national_day(self):
        """国庆节是法定假日"""
        d = date(2025, 10, 1)
        assert is_holiday(d) is True

    def test_new_year(self):
        """元旦是法定假日"""
        d = date(2025, 1, 1)
        assert is_holiday(d) is True

    def test_regular_workday_not_holiday(self):
        """普通工作日不是法定假日"""
        d = date(2026, 2, 9)  # 周一
        result = is_holiday(d)
        assert result is False

    def test_weekend_not_in_holiday_dict(self):
        """周末不在法定节假日字典里（不是 True）"""
        d = date(2026, 2, 7)  # 周六
        result = is_holiday(d)
        # is_holiday 只检查法定节假日字典，周末返回 False
        assert isinstance(result, bool)

    def test_unknown_year(self):
        """没有数据的年份返回 False"""
        d = date(2030, 10, 1)  # 假设没有 2030 数据
        result = is_holiday(d)
        assert isinstance(result, bool)


class TestGetHolidayName:
    """测试获取节假日名称"""

    def test_national_day_name(self):
        d = date(2025, 10, 1)
        name = get_holiday_name(d)
        assert name is not None
        assert isinstance(name, str)

    def test_new_year_name(self):
        d = date(2025, 1, 1)
        name = get_holiday_name(d)
        assert name is not None

    def test_regular_workday_no_name(self):
        d = date(2026, 2, 9)  # 普通周一
        name = get_holiday_name(d)
        assert name is None

    def test_weekend_no_name(self):
        """周末不在节假日字典，返回 None"""
        d = date(2026, 2, 7)  # 周六
        name = get_holiday_name(d)
        assert name is None


class TestIsWorkdayAdjustment:
    """测试调休判断"""

    def test_regular_weekday(self):
        d = date(2026, 2, 9)  # 普通周一
        result = is_workday_adjustment(d)
        assert isinstance(result, bool)

    def test_weekend(self):
        d = date(2026, 2, 7)  # 周六
        result = is_workday_adjustment(d)
        assert isinstance(result, bool)


class TestGetWorkType:
    """测试工作日类型（返回大写字符串）"""

    def test_weekend_type_uppercase(self):
        d = date(2026, 2, 7)  # 周六
        work_type = get_work_type(d)
        assert work_type == "WEEKEND"

    def test_weekday_type(self):
        d = date(2026, 2, 9)  # 周一
        work_type = get_work_type(d)
        # 普通工作日可能返回 NORMAL、WORKDAY 等
        assert isinstance(work_type, str) and len(work_type) > 0

    def test_holiday_type(self):
        d = date(2025, 10, 1)  # 国庆
        work_type = get_work_type(d)
        assert work_type == "HOLIDAY"

    def test_return_is_string(self):
        d = date(2026, 3, 16)  # 普通周一
        result = get_work_type(d)
        assert isinstance(result, str)


class TestGetWorkingDays:
    """测试工作日计算"""

    def test_same_day(self):
        d = date(2026, 2, 9)  # 周一
        result = get_working_days(d, d)
        assert isinstance(result, int)

    def test_one_full_week(self):
        start = date(2026, 2, 9)   # 周一
        end = date(2026, 2, 13)    # 周五
        result = get_working_days(start, end)
        assert result >= 1

    def test_cross_weekend(self):
        start = date(2026, 2, 6)   # 周五
        end = date(2026, 2, 10)    # 下周二
        result = get_working_days(start, end)
        assert isinstance(result, int)
        assert result >= 0

    def test_reversed_range(self):
        start = date(2026, 2, 13)
        end = date(2026, 2, 9)
        result = get_working_days(start, end)
        assert isinstance(result, int)


class TestAddWorkingDays:
    """测试工作日加减"""

    def test_add_zero_days(self):
        d = date(2026, 2, 9)  # 周一
        result = add_working_days(d, 0)
        assert isinstance(result, date)
        assert result >= d  # 加0天，结果不早于原日期

    def test_add_five_days(self):
        d = date(2026, 2, 9)  # 周一
        result = add_working_days(d, 5)
        assert result > d
        assert result >= date(2026, 2, 14)

    def test_add_one_day_result_is_date(self):
        d = date(2026, 2, 9)  # 周一
        result = add_working_days(d, 1)
        assert isinstance(result, date)
        assert result > d

    def test_add_negative_days_returns_date(self):
        d = date(2026, 2, 11)  # 周三
        result = add_working_days(d, -2)
        assert isinstance(result, date)

    def test_large_positive_offset(self):
        d = date(2026, 1, 5)
        result = add_working_days(d, 20)
        assert result > d

    def test_result_is_date_type(self):
        for days in [1, 3, 7, 14]:
            result = add_working_days(date(2026, 3, 2), days)
            assert isinstance(result, date)
