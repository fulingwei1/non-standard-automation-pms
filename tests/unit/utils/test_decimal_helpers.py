# -*- coding: utf-8 -*-
"""
Decimal 工具函数测试
"""

from decimal import Decimal

import pytest

from app.utils.decimal_helpers import (
    HUNDRED,
    ONE,
    ZERO,
    decimal_from_percentage,
    ensure_decimal,
    parse_decimal,
    quantize_decimal,
    safe_decimal_from_dict,
    sum_decimals,
)


class TestParseDecimal:
    """parse_decimal 函数测试"""

    def test_parse_none_returns_default(self):
        assert parse_decimal(None) == ZERO
        assert parse_decimal(None, default="10") == Decimal("10")

    def test_parse_empty_string_returns_default(self):
        assert parse_decimal("") == ZERO
        assert parse_decimal("", default="5") == Decimal("5")

    def test_parse_decimal_returns_same(self):
        value = Decimal("123.45")
        assert parse_decimal(value) == value

    def test_parse_int(self):
        assert parse_decimal(100) == Decimal("100")

    def test_parse_float(self):
        result = parse_decimal(3.14)
        assert result == Decimal("3.14")

    def test_parse_string(self):
        assert parse_decimal("99.99") == Decimal("99.99")

    def test_parse_invalid_returns_default(self):
        assert parse_decimal("invalid") == ZERO
        assert parse_decimal("abc", default="1") == Decimal("1")

    def test_parse_negative(self):
        assert parse_decimal("-50.5") == Decimal("-50.5")


class TestDecimalFromPercentage:
    """decimal_from_percentage 函数测试"""

    def test_basic_percentage(self):
        base = Decimal("1000")
        result = decimal_from_percentage(10, base)
        assert result == Decimal("100.00")

    def test_percentage_with_places(self):
        base = Decimal("1000")
        result = decimal_from_percentage(33.33, base, places=4)
        assert result == Decimal("333.3000")

    def test_zero_percentage(self):
        base = Decimal("1000")
        result = decimal_from_percentage(0, base)
        assert result == ZERO

    def test_none_percentage(self):
        base = Decimal("1000")
        result = decimal_from_percentage(None, base)
        assert result == ZERO


class TestSafeDecimalFromDict:
    """safe_decimal_from_dict 函数测试"""

    def test_existing_key(self):
        data = {"amount": "123.45"}
        assert safe_decimal_from_dict(data, "amount") == Decimal("123.45")

    def test_missing_key(self):
        data = {"other": "value"}
        assert safe_decimal_from_dict(data, "amount") == ZERO

    def test_missing_key_with_default(self):
        data = {}
        assert safe_decimal_from_dict(data, "amount", default="100") == Decimal("100")

    def test_none_value(self):
        data = {"amount": None}
        assert safe_decimal_from_dict(data, "amount") == ZERO


class TestQuantizeDecimal:
    """quantize_decimal 函数测试"""

    def test_default_places(self):
        value = Decimal("123.456789")
        result = quantize_decimal(value)
        assert result == Decimal("123.46")

    def test_custom_places(self):
        value = Decimal("123.456789")
        assert quantize_decimal(value, places=4) == Decimal("123.4568")
        assert quantize_decimal(value, places=0) == Decimal("123")

    def test_rounding(self):
        assert quantize_decimal(Decimal("1.555"), places=2) == Decimal("1.56")
        assert quantize_decimal(Decimal("1.554"), places=2) == Decimal("1.55")


class TestEnsureDecimal:
    """ensure_decimal 函数测试"""

    def test_decimal_passthrough(self):
        value = Decimal("100")
        assert ensure_decimal(value) is value

    def test_int_conversion(self):
        result = ensure_decimal(100)
        assert result == Decimal("100")
        assert isinstance(result, Decimal)

    def test_float_conversion(self):
        result = ensure_decimal(3.14)
        assert isinstance(result, Decimal)

    def test_string_conversion(self):
        result = ensure_decimal("99.99")
        assert result == Decimal("99.99")


class TestSumDecimals:
    """sum_decimals 函数测试"""

    def test_sum_varargs(self):
        # sum_decimals 使用 *values 参数
        assert sum_decimals(Decimal("10"), Decimal("20"), Decimal("30")) == Decimal("60")

    def test_sum_empty(self):
        assert sum_decimals() == ZERO

    def test_sum_mixed_types(self):
        assert sum_decimals(10, "20", Decimal("30")) == Decimal("60")

    def test_sum_with_none(self):
        assert sum_decimals(10, None, 20) == Decimal("30")


class TestConstants:
    """常量测试"""

    def test_zero(self):
        assert ZERO == Decimal("0")

    def test_one(self):
        assert ONE == Decimal("1")

    def test_hundred(self):
        assert HUNDRED == Decimal("100")
