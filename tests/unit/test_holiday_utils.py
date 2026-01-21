# -*- coding: utf-8 -*-
"""
节假日工具模块单元测试
"""

from datetime import date


from app.utils.holiday_utils import (
    CHINESE_HOLIDAYS,
    WORKDAY_ADJUSTMENTS,
    get_holiday_name,
    get_work_type,
    is_holiday,
    is_workday_adjustment,
)


class TestIsHoliday:
    """is_holiday 函数测试"""

    def test_2025_spring_festival(self):
        """测试 2025 年春节假期"""
        holiday_date = date(2025, 1, 29)
        assert is_holiday(holiday_date) is True

    def test_2025_new_year(self):
        """测试 2025 年元旦"""
        new_year = date(2025, 1, 1)
        assert is_holiday(new_year) is True

    def test_2025_qingming(self):
        """测试 2025 年清明节"""
        qingming = date(2025, 4, 5)
        assert is_holiday(qingming) is True

    def test_2025_labor_day(self):
        """测试 2025 年劳动节"""
        labor_day = date(2025, 5, 1)
        assert is_holiday(labor_day) is True

    def test_2025_dragon_boat(self):
        """测试 2025 年端午节"""
        dragon_boat = date(2025, 6, 1)
        assert is_holiday(dragon_boat) is True

    def test_2025_national_day(self):
        """测试 2025 年国庆节"""
        national_day = date(2025, 10, 1)
        assert is_holiday(national_day) is True

    def test_2025_mid_autumn(self):
        """测试 2025 年中秋节"""
        mid_autumn = date(2025, 10, 4)
        assert is_holiday(mid_autumn) is True

    def test_2026_spring_festival(self):
        """测试 2026 年春节假期"""
        holiday_date = date(2026, 2, 17)
        assert is_holiday(holiday_date) is True

    def test_2026_new_year(self):
        """测试 2026 年元旦"""
        new_year = date(2026, 1, 1)
        assert is_holiday(new_year) is True

    def test_2026_qingming(self):
        """测试 2026 年清明节"""
        qingming = date(2026, 4, 5)
        assert is_holiday(qingming) is True

    def test_2026_labor_day(self):
        """测试 2026 年劳动节"""
        labor_day = date(2026, 5, 1)
        assert is_holiday(labor_day) is True

    def test_2026_dragon_boat(self):
        """测试 2026 年端午节"""
        dragon_boat = date(2026, 6, 20)
        assert is_holiday(dragon_boat) is True

    def test_2026_mid_autumn(self):
        """测试 2026 年中秋节"""
        mid_autumn = date(2026, 9, 26)
        assert is_holiday(mid_autumn) is True

    def test_2026_national_day(self):
        """测试 2026 年国庆节"""
        national_day = date(2026, 10, 1)
        assert is_holiday(national_day) is True

    def test_non_holiday(self):
        """测试非节假日"""
        regular_day = date(2025, 3, 15)
        assert is_holiday(regular_day) is False

    def test_year_not_in_config(self):
        """测试未配置的年份"""
        future_date = date(2027, 1, 1)
        assert is_holiday(future_date) is False


class TestGetHolidayName:
    """get_holiday_name 函数测试"""

    def test_get_spring_festival_name(self):
        """测试获取春节名称"""
        holiday_date = date(2025, 1, 29)
        name = get_holiday_name(holiday_date)
        assert name == "春节"

    def test_get_new_year_name(self):
        """测试获取元旦名称"""
        new_year = date(2025, 1, 1)
        name = get_holiday_name(new_year)
        assert name == "元旦"

    def test_get_qingming_name(self):
        """测试获取清明节名称"""
        qingming = date(2025, 4, 5)
        name = get_holiday_name(qingming)
        assert name == "清明节"

    def test_get_labor_day_name(self):
        """测试获取劳动节名称"""
        labor_day = date(2025, 5, 1)
        name = get_holiday_name(labor_day)
        assert name == "劳动节"

    def test_get_national_day_name(self):
        """测试获取国庆节名称"""
        national_day = date(2025, 10, 1)
        name = get_holiday_name(national_day)
        assert name == "国庆节"

    def test_get_mid_autumn_name(self):
        """测试获取中秋节名称"""
        mid_autumn = date(2025, 10, 4)
        name = get_holiday_name(mid_autumn)
        assert name == "中秋节"

    def test_non_holiday_returns_none(self):
        """测试非节假日返回 None"""
        regular_day = date(2025, 3, 15)
        name = get_holiday_name(regular_day)
        assert name is None


class TestIsWorkdayAdjustment:
    """is_workday_adjustment 函数测试"""

    def test_2025_workday_adjustment_spring_festival(self):
        """测试 2025 年春节调休工作日"""
        adjustment_date = date(2025, 1, 26)
        assert is_workday_adjustment(adjustment_date) is True

    def test_2025_workday_adjustment_spring_festival_2(self):
        """测试 2025 年春节第二次调休工作日"""
        adjustment_date = date(2025, 2, 8)
        assert is_workday_adjustment(adjustment_date) is True

    def test_2025_workday_adjustment_labor_day(self):
        """测试 2025 年劳动节调休工作日"""
        adjustment_date = date(2025, 4, 27)
        assert is_workday_adjustment(adjustment_date) is True

    def test_2025_workday_adjustment_national_day(self):
        """测试 2025 年国庆节调休工作日"""
        adjustment_date = date(2025, 9, 28)
        assert is_workday_adjustment(adjustment_date) is True

    def test_2026_workday_adjustment_spring_festival(self):
        """测试 2026 年春节调休工作日"""
        adjustment_date = date(2026, 2, 14)
        assert is_workday_adjustment(adjustment_date) is True

    def test_2026_workday_adjustment_spring_festival_2(self):
        """测试 2026 年春节第二次调休工作日"""
        adjustment_date = date(2026, 2, 28)
        assert is_workday_adjustment(adjustment_date) is True

    def test_non_adjustment_day(self):
        """测试非调休工作日"""
        regular_day = date(2025, 3, 15)
        assert is_workday_adjustment(regular_day) is False


class TestGetWorkType:
    """get_work_type 函数测试"""

    def test_holiday_returns_holiday(self):
        """测试节假日返回 HOLIDAY"""
        holiday_date = date(2025, 10, 1)
        work_type = get_work_type(holiday_date)
        assert work_type == "HOLIDAY"

    def test_workday_adjustment_returns_normal(self):
        """测试调休工作日返回 NORMAL"""
        adjustment_date = date(2025, 1, 26)
        work_type = get_work_type(adjustment_date)
        assert work_type == "NORMAL"

    def test_saturday_returns_weekend(self):
        """测试周六返回 WEEKEND"""
        saturday = date(2025, 3, 15)
        assert saturday.weekday() == 5
        work_type = get_work_type(saturday)
        assert work_type == "WEEKEND"

    def test_sunday_returns_weekend(self):
        """测试周日返回 WEEKEND"""
        sunday = date(2025, 3, 16)
        assert sunday.weekday() == 6
        work_type = get_work_type(sunday)
        assert work_type == "WEEKEND"

    def test_monday_returns_normal(self):
        """测试周一返回 NORMAL"""
        monday = date(2025, 3, 17)
        assert monday.weekday() == 0
        work_type = get_work_type(monday)
        assert work_type == "NORMAL"

    def test_tuesday_returns_normal(self):
        """测试周二返回 NORMAL"""
        tuesday = date(2025, 3, 18)
        assert tuesday.weekday() == 1
        work_type = get_work_type(tuesday)
        assert work_type == "NORMAL"

    def test_wednesday_returns_normal(self):
        """测试周三返回 NORMAL"""
        wednesday = date(2025, 3, 19)
        assert wednesday.weekday() == 2
        work_type = get_work_type(wednesday)
        assert work_type == "NORMAL"

    def test_thursday_returns_normal(self):
        """测试周四返回 NORMAL"""
        thursday = date(2025, 3, 20)
        assert thursday.weekday() == 3
        work_type = get_work_type(thursday)
        assert work_type == "NORMAL"

    def test_friday_returns_normal(self):
        """测试周五返回 NORMAL"""
        friday = date(2025, 3, 21)
        assert friday.weekday() == 4
        work_type = get_work_type(friday)
        assert work_type == "NORMAL"

    def test_saturday_on_holiday_returns_holiday(self):
        """测试周六是节假日时返回 HOLIDAY"""
        saturday_holiday = date(2025, 10, 4)
        assert saturday_holiday.weekday() == 5
        work_type = get_work_type(saturday_holiday)
        assert work_type == "HOLIDAY"

    def test_sunday_on_holiday_returns_holiday(self):
        """测试周日是节假日时返回 HOLIDAY"""
        sunday_holiday = date(2025, 10, 5)
        assert sunday_holiday.weekday() == 6
        work_type = get_work_type(sunday_holiday)
        assert work_type == "HOLIDAY"


class TestHolidayDataStructure:
    """测试节假日数据结构"""

    def test_chinese_holidays_is_dict(self):
        """测试 CHINESE_HOLIDAYS 是字典"""
        assert isinstance(CHINESE_HOLIDAYS, dict)

    def test_chinese_holidays_has_2025(self):
        """测试 CHINESE_HOLIDAYS 包含 2025 年"""
        assert 2025 in CHINESE_HOLIDAYS

    def test_chinese_holidays_has_2026(self):
        """测试 CHINESE_HOLIDAYS 包含 2026 年"""
        assert 2026 in CHINESE_HOLIDAYS

    def test_chinese_holidays_2025_is_dict(self):
        """测试 2025 年数据是字典"""
        assert isinstance(CHINESE_HOLIDAYS[2025], dict)

    def test_chinese_holidays_values_are_dates(self):
        """测试节假日键是 date 对象"""
        holidays_2025 = CHINESE_HOLIDAYS[2025]
        for holiday_date in holidays_2025.keys():
            assert isinstance(holiday_date, date)

    def test_chinese_holidays_values_are_strings(self):
        """测试节假日值是字符串"""
        holidays_2025 = CHINESE_HOLIDAYS[2025]
        for holiday_name in holidays_2025.values():
            assert isinstance(holiday_name, str)
            assert len(holiday_name) > 0

    def test_workday_adjustments_is_dict(self):
        """测试 WORKDAY_ADJUSTMENTS 是字典"""
        assert isinstance(WORKDAY_ADJUSTMENTS, dict)

    def test_workday_adjustments_has_2025(self):
        """测试 WORKDAY_ADJUSTMENTS 包含 2025 年"""
        assert 2025 in WORKDAY_ADJUSTMENTS

    def test_workday_adjustments_has_2026(self):
        """测试 WORKDAY_ADJUSTMENTS 包含 2026 年"""
        assert 2026 in WORKDAY_ADJUSTMENTS

    def test_workday_adjustments_values_are_sets(self):
        """测试调休数据是集合"""
        adjustments_2025 = WORKDAY_ADJUSTMENTS[2025]
        assert isinstance(adjustments_2025, set)

    def test_workday_adjustments_dates_are_dates(self):
        """测试调休键是 date 对象"""
        adjustments_2025 = WORKDAY_ADJUSTMENTS[2025]
        for adjustment_date in adjustments_2025:
            assert isinstance(adjustment_date, date)
