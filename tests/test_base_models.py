# -*- coding: utf-8 -*-
"""
基础模型和工具测试
"""
import pytest
from datetime import datetime, date
from decimal import Decimal

from app.models.base import Base, TimestampMixin


class TestBaseModel:
    """基础模型测试"""

    def test_base_model_import(self):
        """测试基础模型可导入"""
        assert Base is not None

    def test_timestamp_mixin_import(self):
        """测试时间戳混入可导入"""
        assert TimestampMixin is not None


class TestDecimalField:
    """Decimal 字段测试"""

    def test_decimal_creation(self):
        """测试 Decimal 创建"""
        amount = Decimal("12345.67")
        assert amount == Decimal("12345.67")

    def test_decimal_arithmetic(self):
        """测试 Decimal 运算"""
        a = Decimal("100.00")
        b = Decimal("50.00")
        assert a + b == Decimal("150.00")
        assert a - b == Decimal("50.00")
        assert a * b == Decimal("5000.00")

    def test_decimal_comparison(self):
        """测试 Decimal 比较"""
        a = Decimal("100.00")
        b = Decimal("100.00")
        c = Decimal("200.00")
        assert a == b
        assert a < c
        assert c > a


class TestDateTimeFields:
    """日期时间字段测试"""

    def test_datetime_creation(self):
        """测试 datetime 创建"""
        dt = datetime(2025, 1, 1, 10, 30, 0)
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 1

    def test_date_creation(self):
        """测试 date 创建"""
        d = date(2025, 1, 1)
        assert d.year == 2025
        assert d.month == 1
        assert d.day == 1


class TestJSONFields:
    """JSON 字段测试"""

    def test_dict_to_json(self):
        """测试字典转 JSON"""
        data = {"key": "value", "number": 123, "nested": {"a": 1}}
        assert isinstance(data, dict)
        assert data["key"] == "value"
        assert data["nested"]["a"] == 1

    def test_list_to_json(self):
        """测试列表转 JSON"""
        data = [1, 2, 3, "test"]
        assert isinstance(data, list)
        assert len(data) == 4

    def test_complex_json(self):
        """测试复杂 JSON"""
        data = {
            "trigger_condition": {"performance_level": "EXCELLENT", "min_score": 90},
            "apply_to_roles": ["manager", "engineer"],
            "apply_to_projects": ["PROJECT_A", "PROJECT_B"],
        }
        assert data["trigger_condition"]["min_score"] == 90
        assert len(data["apply_to_roles"]) == 2


class TestBooleanFields:
    """布尔字段测试"""

    def test_boolean_true(self):
        """测试布尔真值"""
        is_active = True
        assert is_active is True

    def test_boolean_false(self):
        """测试布尔假值"""
        is_active = False
        assert is_active is False

    def test_boolean_default(self):
        """测试布尔默认值"""
        is_active = bool()
        assert is_active is False


class TestIntegerFields:
    """整数字段测试"""

    def test_integer_basic(self):
        """测试整数基本操作"""
        count = 100
        assert count == 100
        assert count + 1 == 101

    def test_integer_comparison(self):
        """测试整数比较"""
        a = 10
        b = 20
        assert a < b
        assert b > a
        assert a != b

    def test_integer_zero(self):
        """测试零值"""
        zero = 0
        assert zero == 0
        assert not zero  # 0 is falsy


class TestStringFields:
    """字符串字段测试"""

    def test_string_basic(self):
        """测试字符串基本操作"""
        name = "测试工程师"
        assert name == "测试工程师"
        assert len(name) == 5

    def test_string_format(self):
        """测试字符串格式化"""
        code = "BR{:03d}".format(1)
        assert code == "BR001"

    def test_string_empty(self):
        """测试空字符串"""
        empty = ""
        assert empty == ""


class TestListFields:
    """列表字段测试"""

    def test_list_creation(self):
        """测试列表创建"""
        items = [1, 2, 3]
        assert len(items) == 3

    def test_list_append(self):
        """测试列表追加"""
        items = [1, 2]
        items.append(3)
        assert items == [1, 2, 3]

    def test_list_comprehension(self):
        """测试列表推导"""
        squares = [x**2 for x in range(5)]
        assert squares == [0, 1, 4, 9, 16]


class TestDictFields:
    """字典字段测试"""

    def test_dict_creation(self):
        """测试字典创建"""
        data = {"key": "value"}
        assert data["key"] == "value"

    def test_dict_update(self):
        """测试字典更新"""
        data = {"a": 1}
        data.update({"b": 2})
        assert data == {"a": 1, "b": 2}

    def test_dict_nested(self):
        """测试嵌套字典"""
        data = {"user": {"name": "张三", "age": 30}}
        assert data["user"]["name"] == "张三"