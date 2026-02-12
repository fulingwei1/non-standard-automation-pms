# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/expressions/filters.py"""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock

from app.services.report_framework.expressions.filters import (
    filter_sum_by, filter_avg_by, filter_count_by, filter_group_by,
    filter_sort_by, filter_unique, filter_pluck, filter_currency,
    filter_percentage, filter_round_num, filter_date_format,
    filter_truncate_text, filter_status_label, filter_default_if_none,
    filter_coalesce, register_filters,
)


class TestListFilters:
    def test_sum_by(self):
        items = [{"amount": 10}, {"amount": 20}, {"amount": 30}]
        assert filter_sum_by(items, "amount") == 60

    def test_sum_by_empty(self):
        assert filter_sum_by([], "amount") == 0

    def test_sum_by_none_values(self):
        items = [{"amount": 10}, {"amount": None}, {"amount": 30}]
        assert filter_sum_by(items, "amount") == 40

    def test_avg_by(self):
        items = [{"score": 10}, {"score": 20}, {"score": 30}]
        assert filter_avg_by(items, "score") == 20

    def test_avg_by_empty(self):
        assert filter_avg_by([], "score") == 0

    def test_count_by(self):
        items = [{"status": "DONE"}, {"status": "PENDING"}, {"status": "DONE"}]
        assert filter_count_by(items, "status", "DONE") == 2

    def test_count_by_empty(self):
        assert filter_count_by([], "status", "DONE") == 0

    def test_group_by(self):
        items = [{"cat": "A", "v": 1}, {"cat": "B", "v": 2}, {"cat": "A", "v": 3}]
        result = filter_group_by(items, "cat")
        assert len(result["A"]) == 2
        assert len(result["B"]) == 1

    def test_sort_by(self):
        items = [{"n": 3}, {"n": 1}, {"n": 2}]
        result = filter_sort_by(items, "n")
        assert [r["n"] for r in result] == [1, 2, 3]

    def test_sort_by_reverse(self):
        items = [{"n": 1}, {"n": 3}, {"n": 2}]
        result = filter_sort_by(items, "n", reverse=True)
        assert [r["n"] for r in result] == [3, 2, 1]

    def test_unique(self):
        items = [{"cat": "A"}, {"cat": "B"}, {"cat": "A"}]
        assert filter_unique(items, "cat") == ["A", "B"]

    def test_pluck(self):
        items = [{"id": 1}, {"id": 2}]
        assert filter_pluck(items, "id") == [1, 2]


class TestNumericFilters:
    def test_currency(self):
        assert filter_currency(1234.5) == "¥1,234.50"

    def test_currency_none(self):
        assert filter_currency(None) == "¥0.00"

    def test_currency_custom(self):
        assert filter_currency(100, "$", 0) == "$100"

    def test_percentage(self):
        assert filter_percentage(85.67) == "85.7%"

    def test_percentage_none(self):
        assert filter_percentage(None) == "0%"

    def test_round_num(self):
        assert filter_round_num(3.456, 1) == 3.5

    def test_round_num_none(self):
        assert filter_round_num(None) == 0


class TestDateFilters:
    def test_date_format_date(self):
        d = date(2026, 1, 15)
        assert filter_date_format(d) == "2026-01-15"

    def test_date_format_none(self):
        assert filter_date_format(None) == ""

    def test_date_format_string(self):
        result = filter_date_format("2026-01-15")
        assert "2026" in result


class TestStringFilters:
    def test_truncate_text(self):
        assert filter_truncate_text("hello world", 5) == "hello..."

    def test_truncate_text_short(self):
        assert filter_truncate_text("hi", 5) == "hi"

    def test_truncate_text_none(self):
        assert filter_truncate_text(None) == ""

    def test_status_label(self):
        assert filter_status_label("DONE") == "已完成"
        assert filter_status_label("PENDING") == "待处理"

    def test_status_label_unknown(self):
        assert filter_status_label("UNKNOWN") == "UNKNOWN"

    def test_status_label_none(self):
        assert filter_status_label(None) == ""


class TestConditionFilters:
    def test_default_if_none(self):
        assert filter_default_if_none(None, "default") == "default"
        assert filter_default_if_none("val", "default") == "val"

    def test_coalesce(self):
        assert filter_coalesce(None, None, "third") == "third"
        assert filter_coalesce("first", "second") == "first"
        assert filter_coalesce(None) is None


class TestRegisterFilters:
    def test_register_filters(self):
        env = MagicMock()
        env.filters = {}
        register_filters(env)
        assert "sum_by" in env.filters
        assert "currency" in env.filters
        assert "truncate_text" in env.filters
