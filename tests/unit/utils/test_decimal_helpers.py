# -*- coding: utf-8 -*-
"""
decimal_helpers 单元测试

测试所有 Decimal 工具函数的正确性和边界情况。
"""

import pytest
from decimal import Decimal

from app.utils.decimal_helpers import (
    parse_decimal,
    decimal_from_percentage,
    safe_decimal_from_dict,
    quantize_decimal,
    ensure_decimal,
    sum_decimals,
    ZERO,
    ONE,
    HUNDRED,
)


class TestParseDecimal:
    """parse_decimal 函数测试"""

    def test_parse_string(self):
        """字符串输入"""
        assert parse_decimal("123.45") == Decimal("123.45")
        assert parse_decimal("0") == Decimal("0")
        assert parse_decimal("-99.99") == Decimal("-99.99")

    def test_parse_integer(self):
        """整数输入"""
        assert parse_decimal(100) == Decimal("100")
        assert parse_decimal(0) == Decimal("0")
        assert parse_decimal(-50) == Decimal("-50")

    def test_parse_float(self):
        """浮点数输入"""
        # 注意：浮点数转换可能有精度问题，但结果应该合理
        result = parse_decimal(10.5)
        assert result == Decimal("10.5")

    def test_parse_decimal_passthrough(self):
        """Decimal 类型直接返回"""
        original = Decimal("999.99")
        assert parse_decimal(original) is original

    def test_parse_none_returns_default(self):
        """None 返回默认值"""
        assert parse_decimal(None) == Decimal("0")
        assert parse_decimal(None, default="100") == Decimal("100")

    def test_parse_empty_string_returns_default(self):
        """空字符串返回默认值"""
        assert parse_decimal("") == Decimal("0")
        assert parse_decimal("", default="50") == Decimal("50")

    def test_parse_invalid_returns_default(self):
        """无效输入返回默认值"""
        assert parse_decimal("invalid") == Decimal("0")
        assert parse_decimal("abc123") == Decimal("0")
        assert parse_decimal("invalid", default="100") == Decimal("100")

    def test_parse_negative_default(self):
        """负数默认值"""
        assert parse_decimal(None, default="-10") == Decimal("-10")


class TestDecimalFromPercentage:
    """decimal_from_percentage 函数测试"""

    def test_basic_percentage(self):
        """基础百分比计算"""
        assert decimal_from_percentage(25, Decimal("1000")) == Decimal("250.00")
        assert decimal_from_percentage(50, Decimal("200")) == Decimal("100.00")
        assert decimal_from_percentage(100, Decimal("100")) == Decimal("100.00")

    def test_string_percentage(self):
        """字符串百分比"""
        result = decimal_from_percentage("30.5", Decimal("200"), places=4)
        assert result == Decimal("61.0000")

    def test_zero_percentage(self):
        """零百分比"""
        assert decimal_from_percentage(0, Decimal("1000")) == Decimal("0.00")

    def test_decimal_places(self):
        """不同小数位数"""
        assert decimal_from_percentage(33.33, Decimal("100"), places=2) == Decimal("33.33")
        assert decimal_from_percentage(33.33, Decimal("100"), places=4) == Decimal("33.3300")

    def test_small_percentage(self):
        """小数百分比"""
        assert decimal_from_percentage(0.5, Decimal("1000")) == Decimal("5.00")


class TestSafeDecimalFromDict:
    """safe_decimal_from_dict 函数测试"""

    def test_existing_key(self):
        """存在的键"""
        data = {"price": "99.9", "quantity": 10}
        assert safe_decimal_from_dict(data, "price") == Decimal("99.9")
        assert safe_decimal_from_dict(data, "quantity") == Decimal("10")

    def test_missing_key(self):
        """不存在的键返回默认值"""
        data = {"price": "100"}
        assert safe_decimal_from_dict(data, "cost") == Decimal("0")
        assert safe_decimal_from_dict(data, "cost", default="50") == Decimal("50")

    def test_none_value(self):
        """None 值返回默认值"""
        data = {"price": None}
        assert safe_decimal_from_dict(data, "price") == Decimal("0")

    def test_invalid_value(self):
        """无效值返回默认值"""
        data = {"price": "invalid"}
        assert safe_decimal_from_dict(data, "price") == Decimal("0")

    def test_empty_dict(self):
        """空字典"""
        assert safe_decimal_from_dict({}, "any_key") == Decimal("0")
        assert safe_decimal_from_dict({}, "any_key", default="100") == Decimal("100")


class TestQuantizeDecimal:
    """quantize_decimal 函数测试"""

    def test_basic_quantize(self):
        """基础四舍五入"""
        assert quantize_decimal(Decimal("123.456")) == Decimal("123.46")
        assert quantize_decimal(Decimal("123.454")) == Decimal("123.45")

    def test_different_places(self):
        """不同小数位数"""
        assert quantize_decimal(Decimal("123.456"), places=1) == Decimal("123.5")
        assert quantize_decimal(Decimal("123.456"), places=3) == Decimal("123.456")
        assert quantize_decimal(Decimal("123.456"), places=0) == Decimal("123")

    def test_already_quantized(self):
        """已经是目标精度"""
        assert quantize_decimal(Decimal("100.00"), places=2) == Decimal("100.00")

    def test_whole_number(self):
        """整数输入"""
        assert quantize_decimal(Decimal("100"), places=2) == Decimal("100.00")

    def test_non_decimal_input(self):
        """非 Decimal 输入会被转换"""
        assert quantize_decimal(123.456, places=2) == Decimal("123.46")


class TestEnsureDecimal:
    """ensure_decimal 函数测试"""

    def test_valid_string(self):
        """有效字符串"""
        assert ensure_decimal("123.45") == Decimal("123.45")

    def test_valid_integer(self):
        """有效整数"""
        assert ensure_decimal(100) == Decimal("100")

    def test_decimal_passthrough(self):
        """Decimal 类型直接返回"""
        original = Decimal("999.99")
        assert ensure_decimal(original) is original

    def test_none_raises(self):
        """None 抛出异常"""
        with pytest.raises(ValueError, match="值不能为空"):
            ensure_decimal(None)

    def test_empty_string_raises(self):
        """空字符串抛出异常"""
        with pytest.raises(ValueError, match="值不能为空"):
            ensure_decimal("")

    def test_invalid_string_raises(self):
        """无效字符串抛出异常"""
        with pytest.raises(ValueError, match="无法转换为 Decimal"):
            ensure_decimal("invalid")


class TestSumDecimals:
    """sum_decimals 函数测试"""

    def test_basic_sum(self):
        """基础求和"""
        assert sum_decimals("10", 20, Decimal("30.5")) == Decimal("60.5")

    def test_single_value(self):
        """单个值"""
        assert sum_decimals(100) == Decimal("100")

    def test_no_values(self):
        """无值返回零"""
        assert sum_decimals() == Decimal("0")

    def test_with_invalid_values(self):
        """包含无效值使用默认值"""
        assert sum_decimals("10", "invalid", 20) == Decimal("30")

    def test_custom_default(self):
        """自定义默认值"""
        assert sum_decimals(None, None, default="10") == Decimal("20")

    def test_negative_values(self):
        """负数求和"""
        assert sum_decimals(100, -30, "-20") == Decimal("50")


class TestConstants:
    """常量测试"""

    def test_zero(self):
        assert ZERO == Decimal("0")

    def test_one(self):
        assert ONE == Decimal("1")

    def test_hundred(self):
        assert HUNDRED == Decimal("100")
