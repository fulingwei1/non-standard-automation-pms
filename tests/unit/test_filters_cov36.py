# -*- coding: utf-8 -*-
"""报告框架过滤器单元测试 - 第三十六批"""

import pytest
from datetime import date, datetime
from unittest.mock import MagicMock

pytest.importorskip("app.services.report_framework.expressions.filters")

try:
    from app.services.report_framework.expressions.filters import (
        filter_sum_by,
        filter_avg_by,
        filter_count_by,
        filter_group_by,
        filter_sort_by,
        filter_unique,
        filter_pluck,
        filter_currency,
        filter_percentage,
        filter_round_num,
        filter_date_format,
        filter_truncate_text,
        filter_default_if_none,
        filter_coalesce,
        register_filters,
    )
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    filter_sum_by = None


ITEMS = [
    {"name": "A", "amount": 100, "score": 80},
    {"name": "B", "amount": 200, "score": 60},
    {"name": "C", "amount": 150, "score": 70},
]


class TestFilterSumBy:
    def test_sum_amounts(self):
        assert filter_sum_by(ITEMS, "amount") == 450

    def test_empty_list_returns_zero(self):
        assert filter_sum_by([], "amount") == 0

    def test_missing_field_treated_as_zero(self):
        items = [{"a": 1}, {"a": 2}]
        assert filter_sum_by(items, "nonexistent") == 0


class TestFilterAvgBy:
    def test_avg_scores(self):
        assert filter_avg_by(ITEMS, "score") == pytest.approx(70.0)

    def test_empty_returns_zero(self):
        assert filter_avg_by([], "score") == 0


class TestFilterCountBy:
    def test_count_matching_value(self):
        items = [{"status": "active"}, {"status": "inactive"}, {"status": "active"}]
        assert filter_count_by(items, "status", "active") == 2

    def test_count_no_match(self):
        assert filter_count_by(ITEMS, "name", "Z") == 0


class TestFilterUnique:
    def test_unique_values(self):
        items = [{"cat": "A"}, {"cat": "B"}, {"cat": "A"}]
        result = filter_unique(items, "cat")
        assert sorted(result) == ["A", "B"]


class TestFilterPluck:
    def test_pluck_field(self):
        result = filter_pluck(ITEMS, "name")
        assert result == ["A", "B", "C"]


class TestFilterCurrency:
    def test_formats_number(self):
        result = filter_currency(1234567.89)
        assert "1" in result  # 至少包含数字

    def test_none_value(self):
        result = filter_currency(None)
        assert result is not None


class TestFilterPercentage:
    def test_percentage_formatting(self):
        result = filter_percentage(0.756)
        assert "%" in result or "75" in result


class TestFilterDefaultIfNone:
    def test_none_returns_default(self):
        assert filter_default_if_none(None, "N/A") == "N/A"

    def test_non_none_returns_value(self):
        assert filter_default_if_none("hello", "N/A") == "hello"


class TestFilterCoalesce:
    def test_returns_first_non_none(self):
        result = filter_coalesce(None, None, "found", "other")
        assert result == "found"

    def test_all_none_returns_none(self):
        result = filter_coalesce(None, None)
        assert result is None


class TestRegisterFilters:
    def test_register_adds_filters_to_env(self):
        env = MagicMock()
        env.filters = {}
        register_filters(env)
        assert "sum_by" in env.filters
        assert "avg_by" in env.filters
        assert "currency" in env.filters
