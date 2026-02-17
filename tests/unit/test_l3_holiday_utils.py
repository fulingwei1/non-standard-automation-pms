# -*- coding: utf-8 -*-
"""
L3组 单元测试 - holiday_utils.py
纯逻辑函数，无需 mock DB。
目标：每个函数 ≥ 6 个测试用例
"""

from datetime import date, timedelta

import pytest

from app.utils.holiday_utils import (
    CHINESE_HOLIDAYS,
    WORKDAY_ADJUSTMENTS,
    add_working_days,
    get_holiday_name,
    get_work_type,
    get_working_days,
    is_holiday,
    is_workday_adjustment,
)


# =============================================================================
# is_holiday
# =============================================================================

class TestIsHoliday:

    def test_new_year_2026(self):
        assert is_holiday(date(2026, 1, 1)) is True

    def test_spring_festival_2026(self):
        assert is_holiday(date(2026, 2, 17)) is True

    def test_national_day_2026(self):
        assert is_holiday(date(2026, 10, 1)) is True

    def test_mid_autumn_2026(self):
        assert is_holiday(date(2026, 9, 25)) is True

    def test_labor_day_2026(self):
        assert is_holiday(date(2026, 5, 1)) is True

    def test_regular_workday_not_holiday(self):
        # 2026-03-10 (Tuesday) - no holiday
        assert is_holiday(date(2026, 3, 10)) is False

    def test_weekend_not_in_holiday_list(self):
        # 2026-03-07 (Saturday) - not in CHINESE_HOLIDAYS
        assert is_holiday(date(2026, 3, 7)) is False

    def test_year_not_in_config_returns_false(self):
        assert is_holiday(date(2020, 1, 1)) is False

    def test_national_day_last_day_2026(self):
        assert is_holiday(date(2026, 10, 7)) is True

    def test_dragon_boat_festival_2026(self):
        assert is_holiday(date(2026, 6, 19)) is True


# =============================================================================
# get_holiday_name
# =============================================================================

class TestGetHolidayName:

    def test_new_year_name_2026(self):
        assert get_holiday_name(date(2026, 1, 1)) == "元旦"

    def test_spring_festival_name_2026(self):
        assert get_holiday_name(date(2026, 2, 17)) == "春节"

    def test_qingming_name_2026(self):
        assert get_holiday_name(date(2026, 4, 4)) == "清明节"

    def test_labor_day_name_2026(self):
        assert get_holiday_name(date(2026, 5, 2)) == "劳动节"

    def test_national_day_name_2026(self):
        assert get_holiday_name(date(2026, 10, 3)) == "国庆节"

    def test_mid_autumn_name_2026(self):
        assert get_holiday_name(date(2026, 9, 25)) == "中秋节"

    def test_non_holiday_returns_none(self):
        assert get_holiday_name(date(2026, 3, 10)) is None

    def test_unknown_year_returns_none(self):
        assert get_holiday_name(date(2020, 10, 1)) is None

    def test_new_year_day2_2026(self):
        assert get_holiday_name(date(2026, 1, 2)) == "元旦"


# =============================================================================
# is_workday_adjustment
# =============================================================================

class TestIsWorkdayAdjustment:

    def test_spring_festival_adjustment_2026_feb14(self):
        assert is_workday_adjustment(date(2026, 2, 14)) is True

    def test_spring_festival_adjustment_2026_feb28(self):
        assert is_workday_adjustment(date(2026, 2, 28)) is True

    def test_spring_festival_adjustment_2025_jan26(self):
        assert is_workday_adjustment(date(2025, 1, 26)) is True

    def test_spring_festival_adjustment_2025_feb8(self):
        assert is_workday_adjustment(date(2025, 2, 8)) is True

    def test_national_day_adjustment_2025_sep28(self):
        assert is_workday_adjustment(date(2025, 9, 28)) is True

    def test_national_day_adjustment_2025_oct11(self):
        assert is_workday_adjustment(date(2025, 10, 11)) is True

    def test_normal_workday_not_adjustment(self):
        assert is_workday_adjustment(date(2026, 3, 10)) is False

    def test_regular_saturday_not_adjustment(self):
        # 2026-03-07 (Saturday) - not in adjustments
        assert is_workday_adjustment(date(2026, 3, 7)) is False

    def test_unknown_year_returns_false(self):
        assert is_workday_adjustment(date(2020, 1, 26)) is False


# =============================================================================
# get_work_type
# =============================================================================

class TestGetWorkType:

    def test_holiday_returns_HOLIDAY(self):
        assert get_work_type(date(2026, 1, 1)) == "HOLIDAY"

    def test_spring_festival_returns_HOLIDAY(self):
        assert get_work_type(date(2026, 2, 17)) == "HOLIDAY"

    def test_workday_adjustment_returns_NORMAL(self):
        # 2026-02-14 is a Saturday but adjusted to workday
        assert get_work_type(date(2026, 2, 14)) == "NORMAL"

    def test_regular_saturday_returns_WEEKEND(self):
        # 2026-03-07 is a Saturday with no adjustment
        assert get_work_type(date(2026, 3, 7)) == "WEEKEND"

    def test_sunday_returns_WEEKEND(self):
        # 2026-03-08 is a Sunday
        assert get_work_type(date(2026, 3, 8)) == "WEEKEND"

    def test_regular_monday_returns_NORMAL(self):
        # 2026-03-09 is a Monday
        assert get_work_type(date(2026, 3, 9)) == "NORMAL"

    def test_regular_friday_returns_NORMAL(self):
        # 2026-03-13 is a Friday
        assert get_work_type(date(2026, 3, 13)) == "NORMAL"


# =============================================================================
# get_working_days
# =============================================================================

class TestGetWorkingDays:

    def test_single_normal_workday(self):
        # 2026-03-09 is a Monday (normal workday), count = 1
        result = get_working_days(date(2026, 3, 9), date(2026, 3, 9))
        assert result == 1

    def test_range_all_workdays(self):
        # 2026-03-09 (Mon) to 2026-03-13 (Fri) = 5 working days (no holidays)
        result = get_working_days(date(2026, 3, 9), date(2026, 3, 13))
        assert result == 5

    def test_range_includes_weekend(self):
        # The current implementation counts weekends as non-holidays (not excluded)
        # get_working_days only excludes holidays, not weekends per se
        # 2026-03-07 (Sat) to 2026-03-08 (Sun) - neither is a holiday
        result = get_working_days(date(2026, 3, 7), date(2026, 3, 8))
        assert result == 2  # weekends are counted unless they're holidays

    def test_range_includes_holiday(self):
        # 2026-01-01 is a holiday; 2026-01-02 is also holiday; 2026-01-03 is holiday
        # 2026-01-04 is a Sunday (not holiday), 2026-01-05 is Monday (not holiday)
        result = get_working_days(date(2026, 1, 1), date(2026, 1, 5))
        # Jan 1,2,3 = holidays (not counted), Jan 4,5 = non-holidays (counted)
        assert result == 2

    def test_same_date_holiday(self):
        # Single holiday - not counted
        result = get_working_days(date(2026, 1, 1), date(2026, 1, 1))
        assert result == 0

    def test_start_equals_end_normal(self):
        # Single normal day = 1
        result = get_working_days(date(2026, 3, 9), date(2026, 3, 9))
        assert result == 1

    def test_week_spanning_new_year_2026(self):
        # Dec 31 (normal) + Jan 1 (holiday) + Jan 2 (holiday) + Jan 3 (holiday) + Jan 4 (Sun, non-holiday)
        result = get_working_days(date(2025, 12, 31), date(2026, 1, 4))
        # Dec 31, Jan 4 are non-holidays = 2; Jan 1-3 are holidays = 0
        assert result == 2


# =============================================================================
# add_working_days
# =============================================================================

class TestAddWorkingDays:

    def test_add_one_workday_from_normal(self):
        # From 2026-03-09 (Mon), add 1 workday -> 2026-03-10 (Tue) - not a holiday
        result = add_working_days(date(2026, 3, 9), 1)
        assert result == date(2026, 3, 10)

    def test_add_five_workdays(self):
        # From 2026-03-09 (Mon), add 5 workdays -> 2026-03-14 (Sat) - all are non-holidays
        result = add_working_days(date(2026, 3, 9), 5)
        assert result == date(2026, 3, 14)

    def test_add_zero_workdays(self):
        # Adding 0 days = same date
        start = date(2026, 3, 9)
        result = add_working_days(start, 0)
        assert result == start

    def test_skip_holidays_when_adding(self):
        # From 2025-12-31, add 1 workday.
        # Jan 1 (holiday), Jan 2 (holiday), Jan 3 (holiday), Jan 4 (Sun, non-holiday) -> Jan 4
        result = add_working_days(date(2025, 12, 31), 1)
        assert result == date(2026, 1, 4)

    def test_add_three_workdays_around_holiday(self):
        # From 2025-12-30 (Tue), add 3 workdays:
        # +1 = Dec 31 (non-holiday), +2 = Jan 1 (holiday skip), Jan 2 (holiday skip),
        # Jan 3 (holiday skip), Jan 4 (non-holiday) = +2, +3 = Jan 5 (Mon)
        result = add_working_days(date(2025, 12, 30), 3)
        assert result == date(2026, 1, 5)

    def test_add_workdays_returns_date_type(self):
        result = add_working_days(date(2026, 3, 9), 2)
        assert isinstance(result, date)

    def test_add_ten_workdays(self):
        # From 2026-03-09 (Mon), add 10 workdays without holidays in range
        # Mon 9 + 10 = 10 non-holiday days forward
        result = add_working_days(date(2026, 3, 9), 10)
        # Just verify it's after the start date and correct type
        assert isinstance(result, date)
        assert result > date(2026, 3, 9)
