# -*- coding: utf-8 -*-
"""
Decimal 工具测试
"""

import pytest
from decimal import Decimal


class TestParseDecimal:
    """测试 parse_decimal 函数"""

    def test_parse_decimal_from_string(self):
        """测试从字符串转换"""
        from app.utils.decimal_helpers import parse_decimal

        result = parse_decimal("123.45")
        assert result == Decimal("123.45")

    def test_parse_decimal_from_int(self):
        """测试从整数转换"""
        from app.utils.decimal_helpers import parse_decimal

        result = parse_decimal(123)
        assert result == Decimal("123")

    def test_parse_decimal_from_float(self):
        """测试从浮点数转换"""
        from app.utils.decimal_helpers import parse_decimal

        result = parse_decimal(123.45)
        assert isinstance(result, Decimal)

    def test_parse_decimal_from_decimal(self):
        """测试从 Decimal 转换"""
        from app.utils.decimal_helpers import parse_decimal

        original = Decimal("123.45")
        result = parse_decimal(original)
        assert result == original

    def test_parse_decimal_from_none(self):
        """测试从 None 转换"""
        from app.utils.decimal_helpers import parse_decimal

        result = parse_decimal(None)
        assert result == Decimal("0")

    def test_parse_decimal_default_value(self):
        """测试默认值的自定义"""
        from app.utils.decimal_helpers import parse_decimal

        result = parse_decimal(None, default="100")
        assert result == Decimal("100")

    def test_parse_decimal_invalid_string(self):
        """测试无效字符串"""
        from app.utils.decimal_helpers import parse_decimal

        result = parse_decimal("invalid")
        assert result == Decimal("0")

    def test_parse_decimal_empty_string(self):
        """测试空字符串"""
        from app.utils.decimal_helpers import parse_decimal

        result = parse_decimal("")
        assert result == Decimal("0")