# -*- coding: utf-8 -*-
"""
app/common/ 工具模块覆盖率测试
目标: date_range.py, context.py, query_filters.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock

# ─── date_range.py ───────────────────────────────────────────────────────────

from app.common.date_range import (
    get_month_range,
    get_last_month_range,
    get_month_range_by_ym,
    month_start,
    month_end,
    get_week_range,
)


class TestGetMonthRange:
    def test_january(self):
        start, end = get_month_range(date(2026, 1, 15))
        assert start == date(2026, 1, 1)
        assert end == date(2026, 1, 31)

    def test_february_non_leap(self):
        start, end = get_month_range(date(2025, 2, 10))
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)

    def test_february_leap_year(self):
        start, end = get_month_range(date(2024, 2, 1))
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)

    def test_december(self):
        start, end = get_month_range(date(2025, 12, 25))
        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)

    def test_returns_tuple(self):
        result = get_month_range(date(2026, 3, 5))
        assert len(result) == 2
        assert result[0] <= result[1]


class TestGetLastMonthRange:
    def test_from_february(self):
        start, end = get_last_month_range(date(2026, 2, 15))
        assert start == date(2026, 1, 1)
        assert end == date(2026, 1, 31)

    def test_from_january_wraps_year(self):
        start, end = get_last_month_range(date(2026, 1, 10))
        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)

    def test_from_march(self):
        start, end = get_last_month_range(date(2026, 3, 1))
        assert start == date(2026, 2, 1)
        assert end == date(2026, 2, 28)


class TestGetMonthRangeByYM:
    def test_normal_month(self):
        start, end = get_month_range_by_ym(2026, 4)
        assert start == date(2026, 4, 1)
        assert end == date(2026, 4, 30)

    def test_december(self):
        start, end = get_month_range_by_ym(2025, 12)
        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)

    def test_february_leap(self):
        start, end = get_month_range_by_ym(2024, 2)
        assert end == date(2024, 2, 29)


class TestMonthStartEnd:
    def test_month_start(self):
        assert month_start(date(2026, 5, 20)) == date(2026, 5, 1)

    def test_month_end_30_day(self):
        assert month_end(date(2026, 4, 10)) == date(2026, 4, 30)

    def test_month_end_31_day(self):
        assert month_end(date(2026, 1, 1)) == date(2026, 1, 31)

    def test_month_end_feb(self):
        result = month_end(date(2025, 2, 15))
        assert result == date(2025, 2, 28)


class TestGetWeekRange:
    def test_monday(self):
        d = date(2026, 2, 9)  # 周一
        start, end = get_week_range(d)
        assert start.weekday() == 0  # 周一
        assert end.weekday() == 6    # 周日
        assert (end - start).days == 6

    def test_wednesday(self):
        d = date(2026, 2, 11)  # 周三
        start, end = get_week_range(d)
        assert start == date(2026, 2, 9)  # 本周一
        assert end == date(2026, 2, 15)   # 本周日

    def test_sunday(self):
        d = date(2026, 2, 15)  # 周日
        start, end = get_week_range(d)
        assert start.weekday() == 0
        assert end == d


# ─── context.py ──────────────────────────────────────────────────────────────

from app.common.context import (
    set_audit_context,
    get_audit_context,
    clear_audit_context,
    get_current_tenant_id,
    set_current_tenant_id,
)


class TestAuditContext:
    def test_set_and_get(self):
        set_audit_context(operator_id=42, client_ip="127.0.0.1")
        ctx = get_audit_context()
        assert ctx.get("operator_id") == 42

    def test_clear_context(self):
        set_audit_context(operator_id=1)
        clear_audit_context()
        ctx = get_audit_context()
        assert ctx == {} or ctx.get("operator_id") is None

    def test_get_returns_dict(self):
        clear_audit_context()
        ctx = get_audit_context()
        assert isinstance(ctx, dict)

    def test_overwrite_context(self):
        set_audit_context(operator_id=1)
        set_audit_context(operator_id=2, tenant_id=5)
        ctx = get_audit_context()
        assert ctx.get("operator_id") == 2

    def test_set_with_detail(self):
        set_audit_context(operator_id=10, detail={"action": "login"})
        ctx = get_audit_context()
        assert ctx.get("operator_id") == 10


class TestTenantContext:
    def test_set_and_get(self):
        set_current_tenant_id(99)
        assert get_current_tenant_id() == 99

    def test_set_none(self):
        set_current_tenant_id(None)
        assert get_current_tenant_id() is None

    def test_overwrite(self):
        set_current_tenant_id(10)
        set_current_tenant_id(20)
        assert get_current_tenant_id() == 20


# ─── query_filters.py ────────────────────────────────────────────────────────

from app.common.query_filters import (
    _normalize_keywords,
    build_keyword_conditions,
    apply_pagination,
)


class TestNormalizeKeywords:
    def test_string_input(self):
        result = _normalize_keywords("hello world")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_list_input(self):
        result = _normalize_keywords(["hello", "world"])
        assert isinstance(result, list)

    def test_none_input(self):
        result = _normalize_keywords(None)
        assert result == [] or isinstance(result, list)

    def test_empty_string(self):
        result = _normalize_keywords("")
        assert isinstance(result, list)


class TestApplyPagination:
    # apply_pagination(query, offset, limit) — 直接传 offset 和 limit

    def test_with_nonzero_offset(self):
        """offset > 0 时应该调用 query.offset()"""
        mock_query = MagicMock()
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        apply_pagination(mock_query, offset=20, limit=20)
        mock_query.offset.assert_called_once_with(20)
        mock_query.limit.assert_called_once_with(20)

    def test_zero_offset_skips_offset_call(self):
        """offset == 0 时不调用 query.offset()"""
        mock_query = MagicMock()
        mock_query.limit.return_value = mock_query
        apply_pagination(mock_query, offset=0, limit=10)
        mock_query.offset.assert_not_called()
        mock_query.limit.assert_called_once_with(10)

    def test_zero_limit_skips_limit_call(self):
        """limit == 0 时不调用 query.limit()"""
        mock_query = MagicMock()
        mock_query.offset.return_value = mock_query
        apply_pagination(mock_query, offset=5, limit=0)
        mock_query.limit.assert_not_called()

    def test_returns_query(self):
        mock_query = MagicMock()
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        result = apply_pagination(mock_query, offset=0, limit=10)
        assert result is not None
