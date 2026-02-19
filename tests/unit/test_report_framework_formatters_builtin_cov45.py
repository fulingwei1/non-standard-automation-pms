# -*- coding: utf-8 -*-
"""
第四十五批覆盖：report_framework/formatters/builtin.py
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

pytest.importorskip("app.services.report_framework.formatters.builtin")

from app.services.report_framework.formatters.builtin import (
    format_status_badge,
    format_percentage,
    format_currency,
    format_date,
)


class TestFormatStatusBadge:
    def test_known_completed_status(self):
        result = format_status_badge("COMPLETED")
        assert result["value"] == "COMPLETED"
        assert result["label"] == "已完成"
        assert result["color"] == "green"

    def test_known_in_progress_status(self):
        result = format_status_badge("IN_PROGRESS")
        assert result["label"] == "进行中"
        assert result["color"] == "blue"

    def test_unknown_status_uses_default(self):
        result = format_status_badge("UNKNOWN_XYZ")
        assert result["value"] == "UNKNOWN_XYZ"
        assert result["label"] == "UNKNOWN_XYZ"
        assert result["color"] == "default"

    def test_cancelled_status(self):
        result = format_status_badge("CANCELLED")
        assert result["label"] == "已取消"
        assert result["color"] == "gray"

    def test_rejected_status(self):
        result = format_status_badge("REJECTED")
        assert result["color"] == "red"


class TestFormatPercentage:
    def test_basic_fraction(self):
        result = format_percentage(0.75)
        assert result == "75.0%"

    def test_none_returns_none(self):
        assert format_percentage(None) is None

    def test_custom_decimals(self):
        result = format_percentage(0.3333, decimals=2)
        assert result == "33.33%"

    def test_decimal_type(self):
        result = format_percentage(Decimal("0.5"))
        assert result == "50.0%"

    def test_zero(self):
        result = format_percentage(0)
        assert result == "0.0%"


class TestFormatCurrency:
    def test_basic_currency(self):
        result = format_currency(10000)
        assert result == "¥10,000.00"

    def test_none_returns_none(self):
        assert format_currency(None) is None

    def test_custom_symbol(self):
        result = format_currency(500.5, symbol="$")
        assert result.startswith("$")
        assert "500.50" in result

    def test_decimal_type(self):
        result = format_currency(Decimal("1234.56"))
        assert "1,234.56" in result

    def test_zero_value(self):
        result = format_currency(0)
        assert result == "¥0.00"


class TestFormatDate:
    def test_date_object(self):
        d = date(2024, 3, 15)
        assert format_date(d) == "2024-03-15"

    def test_datetime_object(self):
        dt = datetime(2024, 3, 15, 10, 30, 0)
        assert format_date(dt) == "2024-03-15"

    def test_none_returns_none(self):
        assert format_date(None) is None

    def test_custom_format(self):
        d = date(2024, 3, 15)
        result = format_date(d, fmt="%Y/%m/%d")
        assert result == "2024/03/15"

    def test_year_month_format(self):
        d = date(2024, 6, 1)
        result = format_date(d, fmt="%Y-%m")
        assert result == "2024-06"
