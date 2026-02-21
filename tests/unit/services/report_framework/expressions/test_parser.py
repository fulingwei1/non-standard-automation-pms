# -*- coding: utf-8 -*-
"""
测试 ExpressionParser - 表达式解析器

覆盖率目标: 60%+
测试用例数: 30+
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

from app.services.report_framework.expressions.parser import ExpressionParser, ExpressionError


class TestExpressionParserInit:
    """测试ExpressionParser初始化"""

    def test_init_success(self):
        """测试正常初始化"""
        parser = ExpressionParser()
        assert parser._env is not None

    @patch('app.services.report_framework.expressions.parser.Environment', None)
    def test_init_without_jinja2(self):
        """测试没有jinja2时初始化"""
        parser = ExpressionParser()
        assert parser._env is None


class TestEvaluate:
    """测试表达式计算"""

    def test_evaluate_simple_variable(self):
        """测试简单变量"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ name }}", {"name": "Alice"})
        assert result == "Alice"

    def test_evaluate_arithmetic(self):
        """测试算术运算"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ a + b }}", {"a": 10, "b": 20})
        assert result == 30

    def test_evaluate_division(self):
        """测试除法"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ a / b }}", {"a": 100, "b": 4})
        assert result == 25.0

    def test_evaluate_multiplication(self):
        """测试乘法"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ a * b }}", {"a": 5, "b": 6})
        assert result == 30

    def test_evaluate_string_concatenation(self):
        """测试字符串拼接"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ first ~ ' ' ~ last }}", {"first": "Alice", "last": "Wang"})
        assert result == "Alice Wang"

    def test_evaluate_filter_length(self):
        """测试length过滤器"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ items | length }}", {"items": [1, 2, 3, 4, 5]})
        assert result == 5

    def test_evaluate_no_expression(self):
        """测试非表达式字符串"""
        parser = ExpressionParser()
        result = parser.evaluate("plain text", {})
        assert result == "plain text"

    def test_evaluate_empty_string(self):
        """测试空字符串"""
        parser = ExpressionParser()
        result = parser.evaluate("", {})
        assert result == ""

    def test_evaluate_none(self):
        """测试None"""
        parser = ExpressionParser()
        result = parser.evaluate(None, {})
        assert result is None

    def test_evaluate_syntax_error(self):
        """测试语法错误"""
        parser = ExpressionParser()
        with pytest.raises(ExpressionError, match="Invalid expression syntax"):
            parser.evaluate("{{ invalid syntax }}", {})

    def test_evaluate_undefined_variable(self):
        """测试未定义变量"""
        parser = ExpressionParser()
        # Jinja2默认会抛出UndefinedError，但我们的实现会捕获并转换
        try:
            result = parser.evaluate("{{ undefined_var }}", {})
            # 如果没有抛出异常，应该返回空字符串或引发ExpressionError
            assert result == "" or isinstance(result, str)
        except ExpressionError:
            # 如果抛出ExpressionError也是正确的
            pass

    def test_evaluate_boolean_true(self):
        """测试布尔值True"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ 1 == 1 }}", {})
        assert result is True

    def test_evaluate_boolean_false(self):
        """测试布尔值False"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ 1 == 2 }}", {})
        assert result is False

    def test_evaluate_comparison(self):
        """测试比较运算"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ count > 10 }}", {"count": 15})
        assert result is True


class TestConvertResult:
    """测试结果类型转换"""

    def test_convert_integer(self):
        """测试转换为整数"""
        parser = ExpressionParser()
        result = parser._convert_result("123")
        assert result == 123
        assert isinstance(result, int)

    def test_convert_float(self):
        """测试转换为浮点数"""
        parser = ExpressionParser()
        result = parser._convert_result("123.45")
        assert result == 123.45
        assert isinstance(result, float)

    def test_convert_true(self):
        """测试转换为True"""
        parser = ExpressionParser()
        assert parser._convert_result("true") is True
        assert parser._convert_result("True") is True
        assert parser._convert_result("TRUE") is True

    def test_convert_false(self):
        """测试转换为False"""
        parser = ExpressionParser()
        assert parser._convert_result("false") is False
        assert parser._convert_result("False") is False
        assert parser._convert_result("FALSE") is False

    def test_convert_string(self):
        """测试保持字符串"""
        parser = ExpressionParser()
        result = parser._convert_result("hello world")
        assert result == "hello world"
        assert isinstance(result, str)

    def test_convert_with_whitespace(self):
        """测试带空白字符的转换"""
        parser = ExpressionParser()
        result = parser._convert_result("  123  ")
        assert result == 123


class TestEvaluateDict:
    """测试字典表达式计算"""

    def test_evaluate_dict_simple(self):
        """测试简单字典"""
        parser = ExpressionParser()
        data = {
            "name": "{{ user_name }}",
            "age": "{{ user_age }}"
        }
        result = parser.evaluate_dict(data, {"user_name": "Alice", "user_age": 25})
        assert result["name"] == "Alice"
        assert result["age"] == 25

    def test_evaluate_dict_nested(self):
        """测试嵌套字典"""
        parser = ExpressionParser()
        data = {
            "user": {
                "name": "{{ name }}",
                "profile": {
                    "age": "{{ age }}"
                }
            }
        }
        result = parser.evaluate_dict(data, {"name": "Bob", "age": 30})
        assert result["user"]["name"] == "Bob"
        assert result["user"]["profile"]["age"] == 30

    def test_evaluate_dict_mixed_types(self):
        """测试混合类型"""
        parser = ExpressionParser()
        data = {
            "string": "{{ text }}",
            "number": 123,
            "bool": True,
            "none": None
        }
        result = parser.evaluate_dict(data, {"text": "hello"})
        assert result["string"] == "hello"
        assert result["number"] == 123
        assert result["bool"] is True
        assert result["none"] is None

    def test_evaluate_dict_with_list(self):
        """测试包含列表的字典"""
        parser = ExpressionParser()
        data = {
            "items": ["{{ a }}", "{{ b }}"]
        }
        result = parser.evaluate_dict(data, {"a": 1, "b": 2})
        assert result["items"] == [1, 2]


class TestEvaluateList:
    """测试列表表达式计算"""

    def test_evaluate_list_simple(self):
        """测试简单列表"""
        parser = ExpressionParser()
        data = ["{{ a }}", "{{ b }}", "{{ c }}"]
        result = parser.evaluate_list(data, {"a": 1, "b": 2, "c": 3})
        assert result == [1, 2, 3]

    def test_evaluate_list_nested(self):
        """测试嵌套列表"""
        parser = ExpressionParser()
        data = [
            ["{{ a }}", "{{ b }}"],
            ["{{ c }}", "{{ d }}"]
        ]
        result = parser.evaluate_list(data, {"a": 1, "b": 2, "c": 3, "d": 4})
        assert result == [[1, 2], [3, 4]]

    def test_evaluate_list_with_dict(self):
        """测试包含字典的列表"""
        parser = ExpressionParser()
        data = [
            {"name": "{{ name1 }}"},
            {"name": "{{ name2 }}"}
        ]
        result = parser.evaluate_list(data, {"name1": "Alice", "name2": "Bob"})
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"

    def test_evaluate_list_mixed_types(self):
        """测试混合类型列表"""
        parser = ExpressionParser()
        data = ["{{ text }}", 123, True, None]
        result = parser.evaluate_list(data, {"text": "hello"})
        assert result == ["hello", 123, True, None]


class TestGlobalFunctions:
    """测试全局函数"""

    def test_today_function(self):
        """测试today函数"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ today() }}", {})
        assert isinstance(result, str)  # 转换为字符串

    def test_len_function(self):
        """测试len函数"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ len(items) }}", {"items": [1, 2, 3]})
        assert result == 3

    def test_sum_function(self):
        """测试sum函数"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ sum(numbers) }}", {"numbers": [1, 2, 3, 4, 5]})
        assert result == 15

    def test_min_function(self):
        """测试min函数"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ min(numbers) }}", {"numbers": [5, 2, 8, 1, 9]})
        assert result == 1

    def test_max_function(self):
        """测试max函数"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ max(numbers) }}", {"numbers": [5, 2, 8, 1, 9]})
        assert result == 9

    def test_abs_function(self):
        """测试abs函数"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ abs(num) }}", {"num": -10})
        assert result == 10

    def test_round_function(self):
        """测试round函数"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ round(num, 2) }}", {"num": 3.14159})
        assert result == 3.14


class TestDateFunctions:
    """测试日期快捷函数"""

    def test_last_monday(self):
        """测试上周一"""
        parser = ExpressionParser()
        result = parser._last_monday()
        assert isinstance(result, date)
        assert result.weekday() == 0  # 周一

    def test_last_sunday(self):
        """测试上周日"""
        parser = ExpressionParser()
        result = parser._last_sunday()
        assert isinstance(result, date)
        assert result.weekday() == 6  # 周日

    def test_this_month_start(self):
        """测试本月第一天"""
        parser = ExpressionParser()
        result = parser._this_month_start()
        assert isinstance(result, date)
        assert result.day == 1

    def test_this_month_end(self):
        """测试本月最后一天"""
        parser = ExpressionParser()
        result = parser._this_month_end()
        assert isinstance(result, date)
        # 下个月第一天 - 1天 = 本月最后一天
        next_month_first = (result + timedelta(days=1)).replace(day=1)
        assert result == next_month_first - timedelta(days=1)


class TestEdgeCases:
    """测试边界情况"""

    def test_complex_expression(self):
        """测试复杂表达式"""
        parser = ExpressionParser()
        result = parser.evaluate(
            "{{ (a + b) * c / d }}",
            {"a": 10, "b": 5, "c": 4, "d": 2}
        )
        assert result == 30.0

    def test_string_operations(self):
        """测试字符串操作"""
        parser = ExpressionParser()
        result = parser.evaluate(
            "{{ text | upper }}",
            {"text": "hello"}
        )
        assert result == "HELLO"

    def test_list_comprehension_like(self):
        """测试列表过滤"""
        parser = ExpressionParser()
        # Jinja2不支持列表推导，但支持过滤器
        result = parser.evaluate(
            "{{ items | length }}",
            {"items": [1, 2, 3, 4, 5]}
        )
        assert result == 5

    def test_none_in_expression(self):
        """测试表达式中的None"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ value }}", {"value": None})
        # Jinja2可能将None转为"None"字符串或空字符串，取决于配置
        assert result == "" or result == "None"

    def test_zero_value(self):
        """测试零值"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ count }}", {"count": 0})
        assert result == 0

    def test_negative_number(self):
        """测试负数"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ num }}", {"num": -42})
        assert result == -42

    def test_very_large_number(self):
        """测试大数字"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ num }}", {"num": 999999999})
        assert result == 999999999

    def test_decimal_precision(self):
        """测试小数精度"""
        parser = ExpressionParser()
        result = parser.evaluate("{{ a / b }}", {"a": 1, "b": 3})
        # 浮点数比较
        assert abs(result - 0.333333) < 0.00001

    @patch('app.services.report_framework.expressions.parser.Environment', None)
    def test_evaluate_without_jinja2(self):
        """测试没有jinja2时计算表达式"""
        parser = ExpressionParser()
        with pytest.raises(ExpressionError, match="未安装 jinja2"):
            parser.evaluate("{{ test }}", {})
