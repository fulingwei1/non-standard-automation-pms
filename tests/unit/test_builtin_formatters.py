# -*- coding: utf-8 -*-
from datetime import date, datetime
from decimal import Decimal
from app.services.report_framework.formatters.builtin import (
    format_status_badge, format_percentage, format_currency, format_date
)


class TestFormatStatusBadge:
    def test_known_status(self):
        result = format_status_badge("COMPLETED")
        assert result["label"] == "已完成"
        assert result["color"] == "green"

    def test_unknown_status(self):
        result = format_status_badge("CUSTOM")
        assert result["label"] == "CUSTOM"
        assert result["color"] == "default"


class TestFormatPercentage:
    def test_none(self):
        assert format_percentage(None) is None

    def test_decimal_value(self):
        assert format_percentage(0.75) == "75.0%"

    def test_custom_decimals(self):
        assert format_percentage(0.756, decimals=2) == "75.60%"

    def test_zero(self):
        assert format_percentage(0) == "0.0%"


class TestFormatCurrency:
    def test_none(self):
        assert format_currency(None) is None

    def test_basic(self):
        assert format_currency(10000) == "¥10,000.00"

    def test_custom_symbol(self):
        assert format_currency(1000, symbol="$") == "$1,000.00"

    def test_decimal_input(self):
        assert format_currency(Decimal("1234.5")) == "¥1,234.50"


class TestFormatDate:
    def test_none(self):
        assert format_date(None) is None

    def test_date(self):
        assert format_date(date(2024, 1, 15)) == "2024-01-15"

    def test_datetime_custom_fmt(self):
        assert format_date(datetime(2024, 1, 15, 10, 30), fmt="%Y/%m/%d") == "2024/01/15"
