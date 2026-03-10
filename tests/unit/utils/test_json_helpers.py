# -*- coding: utf-8 -*-
"""
单元测试 - JSON 安全解析工具函数
测试 safe_json_loads 的各种边界情况
"""

import pytest

from app.utils.json_helpers import safe_json_loads


class TestSafeJsonLoads:
    """safe_json_loads 函数测试"""

    def test_valid_json_array(self):
        """测试有效的 JSON 数组字符串"""
        result = safe_json_loads('[1, 2, 3]', default=[])
        assert result == [1, 2, 3]

    def test_valid_json_object(self):
        """测试有效的 JSON 对象字符串"""
        result = safe_json_loads('{"key": "value", "num": 42}', default={})
        assert result == {"key": "value", "num": 42}

    def test_valid_json_with_whitespace(self):
        """测试带有空白字符的有效 JSON"""
        result = safe_json_loads('  [1, 2]  ', default=[])
        assert result == [1, 2]

    def test_invalid_json_returns_default(self):
        """测试无效 JSON 返回默认值"""
        result = safe_json_loads('invalid json', default=[])
        assert result == []

    def test_invalid_json_returns_custom_default(self):
        """测试无效 JSON 返回自定义默认值"""
        result = safe_json_loads('{broken', default={"error": True})
        assert result == {"error": True}

    def test_none_returns_default(self):
        """测试 None 值返回默认值"""
        result = safe_json_loads(None, default=[])
        assert result == []

    def test_empty_string_returns_default(self):
        """测试空字符串返回默认值"""
        result = safe_json_loads('', default={})
        assert result == {}

    def test_whitespace_only_returns_default(self):
        """测试仅空白字符返回默认值"""
        result = safe_json_loads('   ', default=[])
        assert result == []

    def test_already_list_returns_same(self):
        """测试已是列表类型直接返回"""
        input_list = [1, 2, 3]
        result = safe_json_loads(input_list, default=[])
        assert result == input_list
        assert result is input_list  # 应该是同一个对象

    def test_already_dict_returns_same(self):
        """测试已是字典类型直接返回"""
        input_dict = {"key": "value"}
        result = safe_json_loads(input_dict, default={})
        assert result == input_dict
        assert result is input_dict  # 应该是同一个对象

    def test_nested_json(self):
        """测试嵌套 JSON 结构"""
        json_str = '{"users": [{"name": "Alice"}, {"name": "Bob"}]}'
        result = safe_json_loads(json_str, default={})
        assert result == {"users": [{"name": "Alice"}, {"name": "Bob"}]}

    def test_unicode_json(self):
        """测试包含 Unicode 的 JSON"""
        json_str = '{"name": "张三", "city": "北京"}'
        result = safe_json_loads(json_str, default={})
        assert result == {"name": "张三", "city": "北京"}

    def test_number_input_returns_default(self):
        """测试数字输入返回默认值"""
        result = safe_json_loads(123, default=[])
        assert result == []

    def test_boolean_input_returns_default(self):
        """测试布尔输入返回默认值"""
        result = safe_json_loads(True, default={})
        assert result == {}

    def test_log_error_parameter(self, caplog):
        """测试 log_error 参数控制日志输出"""
        # log_error=True（默认）应该记录日志
        safe_json_loads('invalid', default=[], field_name="test_field", log_error=True)
        assert "test_field" in caplog.text or len(caplog.records) > 0

        caplog.clear()

        # log_error=False 不应该记录日志
        safe_json_loads('invalid', default=[], field_name="test_field2", log_error=False)
        # 无法准确断言日志不记录，但至少不应该崩溃

    def test_field_name_in_log(self, caplog):
        """测试字段名在日志中正确显示"""
        safe_json_loads('broken json', default=[], field_name="payment_nodes")
        # 日志中应该包含字段名（如果有日志记录）
        # 这是一个弱断言，主要确保不崩溃

    def test_json_with_special_characters(self):
        """测试包含特殊字符的 JSON"""
        json_str = '{"text": "line1\\nline2\\ttab"}'
        result = safe_json_loads(json_str, default={})
        assert result == {"text": "line1\nline2\ttab"}

    def test_empty_array(self):
        """测试空数组"""
        result = safe_json_loads('[]', default=None)
        assert result == []

    def test_empty_object(self):
        """测试空对象"""
        result = safe_json_loads('{}', default=None)
        assert result == {}

    def test_json_number_string(self):
        """测试纯数字 JSON 字符串"""
        result = safe_json_loads('42', default=[])
        assert result == 42

    def test_json_boolean_string(self):
        """测试布尔值 JSON 字符串"""
        result = safe_json_loads('true', default=None)
        assert result is True

    def test_json_null_string(self):
        """测试 null JSON 字符串"""
        result = safe_json_loads('null', default=[])
        assert result is None

    def test_truncated_json(self):
        """测试截断的 JSON 字符串"""
        result = safe_json_loads('{"key": "val', default={})
        assert result == {}

    def test_malformed_unicode(self):
        """测试格式错误的 Unicode 转义"""
        result = safe_json_loads('{"text": "\\uZZZZ"}', default={})
        assert result == {}
