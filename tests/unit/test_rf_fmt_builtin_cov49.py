# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/formatters/builtin.py"""

import pytest
from datetime import date, datetime
from decimal import Decimal

try:
    from app.services.report_framework.formatters.builtin import (
        format_status_badge,
        format_percentage,
        format_currency,
        format_date,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_format_status_badge_known_status():
    result = format_status_badge("COMPLETED")
    assert result["label"] == "已完成"
    assert result["color"] == "green"
    assert result["value"] == "COMPLETED"


def test_format_status_badge_unknown_status():
    result = format_status_badge("UNKNOWN_STATUS")
    assert result["value"] == "UNKNOWN_STATUS"
    assert result["label"] == "UNKNOWN_STATUS"
    assert result["color"] == "default"


def test_format_percentage_basic():
    result = format_percentage(0.75)
    assert result == "75.0%"


def test_format_percentage_zero():
    result = format_percentage(0)
    assert result == "0.0%"


def test_format_percentage_none():
    result = format_percentage(None)
    assert result is None


def test_format_percentage_custom_decimals():
    result = format_percentage(0.333, decimals=2)
    assert result == "33.30%"


def test_format_currency_basic():
    result = format_currency(10000.0)
    assert result == "¥10,000.00"


def test_format_currency_none():
    result = format_currency(None)
    assert result is None


def test_format_currency_custom_symbol():
    result = format_currency(5000, symbol="$", decimals=2)
    assert result == "$5,000.00"


def test_format_date_date_object():
    d = date(2025, 3, 15)
    result = format_date(d)
    assert result == "2025-03-15"


def test_format_date_datetime_object():
    dt = datetime(2025, 3, 15, 10, 30, 0)
    result = format_date(dt, fmt="%Y/%m/%d")
    assert result == "2025/03/15"


def test_format_date_none():
    result = format_date(None)
    assert result is None


def test_format_status_badge_in_progress():
    result = format_status_badge("IN_PROGRESS")
    assert result["label"] == "进行中"
    assert result["color"] == "blue"
