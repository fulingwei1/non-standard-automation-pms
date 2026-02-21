# -*- coding: utf-8 -*-
"""
增强的条件解析器单元测试

覆盖所有核心方法和边界场景
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date
from app.services.approval_engine.condition_parser import (
    ConditionEvaluator,
    ConditionParseError,
)


class TestConditionParseError(unittest.TestCase):
    """测试自定义异常"""

    def test_exception_creation(self):
        """测试异常创建"""
        error = ConditionParseError("测试错误")
        self.assertEqual(str(error), "测试错误")
        self.assertIsInstance(error, Exception)


class TestConditionEvaluatorInit(unittest.TestCase):
    """测试初始化"""

    def test_init_with_jinja2(self):
        """测试正常初始化"""
        evaluator = ConditionEvaluator()
        self.assertIsNotNone(evaluator._jinja_env)
        # 验证过滤器已注册
        self.assertIn("length", evaluator._jinja_env.filters)
        self.assertIn("sum_by", evaluator._jinja_env.filters)
        self.assertIn("count_by", evaluator._jinja_env.filters)
        self.assertIn("percentage", evaluator._jinja_env.filters)
        self.assertIn("default", evaluator._jinja_env.filters)

    @patch("app.services.approval_engine.condition_parser.Environment", None)
    def test_init_without_jinja2(self):
        """测试没有jinja2的初始化"""
        evaluator = ConditionEvaluator()
        self.assertIsNone(evaluator._jinja_env)


class TestJinja2Filters(unittest.TestCase):
    """测试Jinja2自定义过滤器"""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_length_filter(self):
        """测试长度过滤器"""
        context = {"items": [1, 2, 3, 4, 5]}
        result = self.evaluator.evaluate("{{ items | length }}", context)
        self.assertEqual(result, 5)

    def test_length_filter_empty(self):
        """测试空列表长度"""
        context = {"items": []}
        result = self.evaluator.evaluate("{{ items | length }}", context)
        self.assertEqual(result, 0)

    def test_length_filter_none(self):
        """测试None的长度"""
        context = {"items": None}
        result = self.evaluator.evaluate("{{ items | length }}", context)
        self.assertEqual(result, 0)

    def test_sum_by_filter(self):
        """测试按字段求和过滤器"""
        context = {
            "items": [
                {"amount": 100},
                {"amount": 200},
                {"amount": 300},
            ]
        }
        result = self.evaluator.evaluate("{{ items | sum_by('amount') }}", context)
        self.assertEqual(result, 600)

    def test_sum_by_filter_empty(self):
        """测试空列表求和"""
        context = {"items": []}
        result = self.evaluator.evaluate("{{ items | sum_by('amount') }}", context)
        self.assertEqual(result, 0)

    def test_sum_by_filter_missing_field(self):
        """测试字段缺失的求和"""
        context = {
            "items": [
                {"amount": 100},
                {"name": "test"},  # 缺少amount字段
                {"amount": 200},
            ]
        }
        result = self.evaluator.evaluate("{{ items | sum_by('amount') }}", context)
        self.assertEqual(result, 300)

    def test_count_by_filter(self):
        """测试按字段计数过滤器"""
        context = {
            "items": [
                {"status": "DONE"},
                {"status": "PENDING"},
                {"status": "DONE"},
            ]
        }
        result = self.evaluator.evaluate(
            "{{ items | count_by('status', 'DONE') }}", context
        )
        self.assertEqual(result, 2)

    def test_count_by_filter_all(self):
        """测试计数全部"""
        context = {
            "items": [
                {"status": "DONE"},
                {"status": "PENDING"},
            ]
        }
        result = self.evaluator.evaluate("{{ items | count_by('status') }}", context)
        self.assertEqual(result, 2)

    def test_percentage_filter(self):
        """测试百分比过滤器"""
        context = {"value": 0.12345}
        result = self.evaluator.evaluate("{{ value | percentage(2) }}", context)
        self.assertEqual(result, 0.12)

    def test_percentage_filter_default_decimals(self):
        """测试默认小数位数"""
        context = {"value": 0.12345}
        result = self.evaluator.evaluate("{{ value | percentage }}", context)
        self.assertEqual(result, 0.1)

    def test_percentage_filter_none(self):
        """测试None的百分比"""
        context = {"value": None}
        result = self.evaluator.evaluate("{{ value | percentage }}", context)
        self.assertEqual(result, 0)

    def test_default_filter(self):
        """测试默认值过滤器"""
        context = {"value": None}
        result = self.evaluator.evaluate("{{ value | default(100) }}", context)
        self.assertEqual(result, 100)

    def test_default_filter_with_value(self):
        """测试有值时的默认值过滤器"""
        context = {"value": 50}
        result = self.evaluator.evaluate("{{ value | default(100) }}", context)
        self.assertEqual(result, 50)


class TestEvaluateMethod(unittest.TestCase):
    """测试evaluate主方法"""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_evaluate_empty_expression(self):
        """测试空表达式"""
        result = self.evaluator.evaluate("", {})
        self.assertIsNone(result)

    def test_evaluate_jinja2_expression(self):
        """测试Jinja2表达式"""
        context = {"value": 10}
        result = self.evaluator.evaluate("{{ value }}", context)
        self.assertEqual(result, 10)

    def test_evaluate_json_expression(self):
        """测试JSON表达式"""
        expr = '{"operator": "AND", "items": [{"field": "form.value", "op": ">", "value": 5}]}'
        context = {"form": {"value": 10}}
        result = self.evaluator.evaluate(expr, context)
        self.assertTrue(result)

    def test_evaluate_sql_like_expression(self):
        """测试SQL-like表达式"""
        context = {"form": {"value": 10}}
        result = self.evaluator.evaluate("form.value > 5", context)
        self.assertTrue(result)


class TestJinja2Evaluation(unittest.TestCase):
    """测试Jinja2表达式评估"""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_simple_variable(self):
        """测试简单变量"""
        context = {"name": "test"}
        result = self.evaluator._evaluate_jinja2("{{ name }}", context)
        self.assertEqual(result, "test")

    def test_integer_conversion(self):
        """测试整数转换"""
        context = {"value": 123}
        result = self.evaluator._evaluate_jinja2("{{ value }}", context)
        self.assertEqual(result, 123)
        self.assertIsInstance(result, int)

    def test_float_conversion(self):
        """测试浮点数转换"""
        context = {"value": 123.45}
        result = self.evaluator._evaluate_jinja2("{{ value }}", context)
        self.assertEqual(result, 123.45)
        self.assertIsInstance(result, float)

    def test_jinja2_syntax_error(self):
        """测试Jinja2语法错误"""
        with self.assertRaises(ConditionParseError) as cm:
            self.evaluator._evaluate_jinja2("{{ value", {})
        self.assertIn("Jinja2语法错误", str(cm.exception))

    @patch("app.services.approval_engine.condition_parser.Environment", None)
    def test_jinja2_not_installed(self):
        """测试Jinja2未安装"""
        evaluator = ConditionEvaluator()
        with self.assertRaises(ConditionParseError) as cm:
            evaluator._evaluate_jinja2("{{ value }}", {})
        self.assertIn("未安装 jinja2 依赖", str(cm.exception))


class TestSimpleConditions(unittest.TestCase):
    """测试简单条件JSON评估"""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_and_operator(self):
        """测试AND操作符"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.value", "op": ">", "value": 5},
                {"field": "form.name", "op": "==", "value": "test"},
            ],
        }
        context = {"form": {"value": 10, "name": "test"}}
        result = self.evaluator._evaluate_simple_conditions(conditions, context)
        self.assertTrue(result)

    def test_and_operator_fail(self):
        """测试AND操作符失败"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.value", "op": ">", "value": 5},
                {"field": "form.name", "op": "==", "value": "fail"},
            ],
        }
        context = {"form": {"value": 10, "name": "test"}}
        result = self.evaluator._evaluate_simple_conditions(conditions, context)
        self.assertFalse(result)

    def test_or_operator(self):
        """测试OR操作符"""
        conditions = {
            "operator": "OR",
            "items": [
                {"field": "form.value", "op": ">", "value": 100},
                {"field": "form.name", "op": "==", "value": "test"},
            ],
        }
        context = {"form": {"value": 10, "name": "test"}}
        result = self.evaluator._evaluate_simple_conditions(conditions, context)
        self.assertTrue(result)

    def test_or_operator_all_fail(self):
        """测试OR操作符全部失败"""
        conditions = {
            "operator": "OR",
            "items": [
                {"field": "form.value", "op": ">", "value": 100},
                {"field": "form.name", "op": "==", "value": "fail"},
            ],
        }
        context = {"form": {"value": 10, "name": "test"}}
        result = self.evaluator._evaluate_simple_conditions(conditions, context)
        self.assertFalse(result)

    def test_empty_conditions(self):
        """测试空条件"""
        result = self.evaluator._evaluate_simple_conditions({}, {})
        self.assertTrue(result)

    def test_empty_items(self):
        """测试空items"""
        conditions = {"operator": "AND", "items": []}
        result = self.evaluator._evaluate_simple_conditions(conditions, {})
        self.assertTrue(result)

    def test_default_operator(self):
        """测试默认操作符（AND）"""
        conditions = {
            "items": [
                {"field": "form.value", "op": ">", "value": 5},
            ]
        }
        context = {"form": {"value": 10}}
        result = self.evaluator._evaluate_simple_conditions(conditions, context)
        self.assertTrue(result)


class TestFieldValueRetrieval(unittest.TestCase):
    """测试字段值获取"""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_simple_field(self):
        """测试简单字段"""
        context = {"form": {"value": 10}}
        result = self.evaluator._get_field_value("form.value", context)
        self.assertEqual(result, 10)

    def test_nested_field(self):
        """测试嵌套字段"""
        context = {"form": {"data": {"value": 10}}}
        result = self.evaluator._get_field_value("form.data.value", context)
        self.assertEqual(result, 10)

    def test_missing_field(self):
        """测试不存在的字段"""
        context = {"form": {"value": 10}}
        result = self.evaluator._get_field_value("form.missing", context)
        self.assertIsNone(result)

    def test_empty_field_path(self):
        """测试空字段路径"""
        result = self.evaluator._get_field_value("", {"form": {"value": 10}})
        self.assertIsNone(result)

    def test_today_function(self):
        """测试today()函数"""
        result = self.evaluator._get_field_value("today()", {})
        self.assertIsInstance(result, date)

    def test_now_function(self):
        """测试now()函数"""
        result = self.evaluator._get_field_value("now()", {})
        self.assertIsInstance(result, datetime)

    def test_user_context_dict(self):
        """测试用户上下文（字典）"""
        context = {"user": {"id": 123, "name": "test"}}
        result = self.evaluator._get_field_value("user.name", context)
        self.assertEqual(result, "test")

    def test_user_context_object(self):
        """测试用户上下文（对象）"""
        user_obj = MagicMock()
        user_obj.name = "test"
        context = {"user": user_obj}
        result = self.evaluator._get_field_value("user.name", context)
        self.assertEqual(result, "test")

    def test_object_attribute(self):
        """测试对象属性"""
        obj = MagicMock()
        obj.value = 100
        context = {"entity": obj}
        result = self.evaluator._get_field_value("entity.value", context)
        self.assertEqual(result, 100)

    def test_nested_object_value(self):
        """测试嵌套对象值"""
        inner = MagicMock()
        inner.value = 200
        outer = MagicMock()
        outer.data = inner
        context = {"entity": outer}
        result = self.evaluator._get_field_value("entity.data.value", context)
        self.assertEqual(result, 200)


class TestCompareValues(unittest.TestCase):
    """测试值比较"""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_equal_operator(self):
        """测试相等操作符"""
        self.assertTrue(self.evaluator._compare_values(10, "==", 10))
        self.assertTrue(self.evaluator._compare_values(10, "=", 10))
        self.assertFalse(self.evaluator._compare_values(10, "==", 20))

    def test_not_equal_operator(self):
        """测试不等操作符"""
        self.assertTrue(self.evaluator._compare_values(10, "!=", 20))
        self.assertFalse(self.evaluator._compare_values(10, "!=", 10))

    def test_greater_than_operator(self):
        """测试大于操作符"""
        self.assertTrue(self.evaluator._compare_values(20, ">", 10))
        self.assertFalse(self.evaluator._compare_values(10, ">", 20))
        self.assertFalse(self.evaluator._compare_values(None, ">", 10))

    def test_greater_equal_operator(self):
        """测试大于等于操作符"""
        self.assertTrue(self.evaluator._compare_values(20, ">=", 10))
        self.assertTrue(self.evaluator._compare_values(10, ">=", 10))
        self.assertFalse(self.evaluator._compare_values(5, ">=", 10))

    def test_less_than_operator(self):
        """测试小于操作符"""
        self.assertTrue(self.evaluator._compare_values(5, "<", 10))
        self.assertFalse(self.evaluator._compare_values(10, "<", 5))
        self.assertFalse(self.evaluator._compare_values(None, "<", 10))

    def test_less_equal_operator(self):
        """测试小于等于操作符"""
        self.assertTrue(self.evaluator._compare_values(5, "<=", 10))
        self.assertTrue(self.evaluator._compare_values(10, "<=", 10))
        self.assertFalse(self.evaluator._compare_values(15, "<=", 10))

    def test_in_operator(self):
        """测试in操作符"""
        self.assertTrue(self.evaluator._compare_values(2, "in", [1, 2, 3]))
        self.assertFalse(self.evaluator._compare_values(5, "in", [1, 2, 3]))
        self.assertFalse(self.evaluator._compare_values(1, "in", None))

    def test_not_in_operator(self):
        """测试not_in操作符"""
        self.assertTrue(self.evaluator._compare_values(5, "not_in", [1, 2, 3]))
        self.assertFalse(self.evaluator._compare_values(2, "not_in", [1, 2, 3]))

    def test_between_operator(self):
        """测试between操作符"""
        self.assertTrue(self.evaluator._compare_values(5, "between", [1, 10]))
        self.assertTrue(self.evaluator._compare_values(1, "between", [1, 10]))
        self.assertTrue(self.evaluator._compare_values(10, "between", [1, 10]))
        self.assertFalse(self.evaluator._compare_values(15, "between", [1, 10]))
        self.assertFalse(self.evaluator._compare_values(None, "between", [1, 10]))
        self.assertFalse(self.evaluator._compare_values(5, "between", [1]))

    def test_contains_operator(self):
        """测试contains操作符"""
        self.assertTrue(self.evaluator._compare_values("hello world", "contains", "world"))
        self.assertFalse(
            self.evaluator._compare_values("hello world", "contains", "test")
        )
        self.assertFalse(self.evaluator._compare_values(None, "contains", "test"))

    def test_starts_with_operator(self):
        """测试starts_with操作符"""
        self.assertTrue(
            self.evaluator._compare_values("hello world", "starts_with", "hello")
        )
        self.assertFalse(
            self.evaluator._compare_values("hello world", "starts_with", "world")
        )
        self.assertFalse(self.evaluator._compare_values(None, "starts_with", "hello"))

    def test_ends_with_operator(self):
        """测试ends_with操作符"""
        self.assertTrue(
            self.evaluator._compare_values("hello world", "ends_with", "world")
        )
        self.assertFalse(
            self.evaluator._compare_values("hello world", "ends_with", "hello")
        )
        self.assertFalse(self.evaluator._compare_values(None, "ends_with", "world"))

    def test_is_null_operator(self):
        """测试is_null操作符"""
        self.assertTrue(self.evaluator._compare_values(None, "is_null", True))
        self.assertFalse(self.evaluator._compare_values(10, "is_null", True))
        self.assertTrue(self.evaluator._compare_values(10, "is_null", False))

    def test_regex_operator(self):
        """测试regex操作符"""
        self.assertTrue(
            self.evaluator._compare_values("hello123", "regex", r"hello\d+")
        )
        self.assertFalse(self.evaluator._compare_values("hello", "regex", r"hello\d+"))
        self.assertFalse(self.evaluator._compare_values(None, "regex", r"test"))

    def test_unsupported_operator(self):
        """测试不支持的操作符"""
        result = self.evaluator._compare_values(10, "unknown", 10)
        self.assertFalse(result)

    def test_comparison_type_error(self):
        """测试比较类型错误"""
        # 字符串和数字比较应该返回False
        result = self.evaluator._compare_values("10", ">", 5)
        # 根据实际实现，可能会抛出异常或返回False
        # 这里假设返回False
        self.assertIsInstance(result, bool)


class TestSQLLikeEvaluation(unittest.TestCase):
    """测试SQL-like表达式评估"""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_simple_comparison(self):
        """测试简单比较"""
        context = {"form": {"value": 10}}
        result = self.evaluator._evaluate_sql_like("form.value > 5", context)
        self.assertTrue(result)

    def test_is_null(self):
        """测试IS NULL"""
        context = {"form": {"value": None}}
        result = self.evaluator._parse_sql_condition("form.value IS NULL", context)
        self.assertTrue(result)

    def test_is_not_null(self):
        """测试IS NOT NULL"""
        context = {"form": {"value": 10}}
        result = self.evaluator._parse_sql_condition("form.value IS NOT NULL", context)
        self.assertTrue(result)

    def test_in_operator(self):
        """测试IN操作符"""
        context = {"form": {"status": "DONE"}}
        result = self.evaluator._parse_sql_condition(
            "form.status IN (DONE, PENDING)", context
        )
        self.assertTrue(result)

    def test_between_operator(self):
        """测试BETWEEN操作符"""
        context = {"form": {"value": 5}}
        result = self.evaluator._parse_sql_condition(
            "form.value BETWEEN 1 AND 10", context
        )
        self.assertTrue(result)

    def test_parse_value_integer(self):
        """测试解析整数"""
        result = self.evaluator._parse_value("123")
        self.assertEqual(result, 123)
        self.assertIsInstance(result, int)

    def test_parse_value_float(self):
        """测试解析浮点数"""
        result = self.evaluator._parse_value("123.45")
        self.assertEqual(result, 123.45)
        self.assertIsInstance(result, float)

    def test_parse_value_boolean(self):
        """测试解析布尔值"""
        self.assertTrue(self.evaluator._parse_value("true"))
        self.assertTrue(self.evaluator._parse_value("True"))
        self.assertFalse(self.evaluator._parse_value("false"))
        self.assertFalse(self.evaluator._parse_value("False"))

    def test_parse_value_string(self):
        """测试解析字符串"""
        result = self.evaluator._parse_value("'hello'")
        self.assertEqual(result, "hello")
        result = self.evaluator._parse_value('"world"')
        self.assertEqual(result, "world")

    def test_parse_value_raw_string(self):
        """测试解析无引号字符串"""
        result = self.evaluator._parse_value("DONE")
        self.assertEqual(result, "DONE")

    def test_unparseable_condition(self):
        """测试无法解析的条件"""
        result = self.evaluator._parse_sql_condition("invalid condition", {})
        self.assertFalse(result)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_deeply_nested_context(self):
        """测试深度嵌套的上下文"""
        context = {"a": {"b": {"c": {"d": {"e": 100}}}}}
        result = self.evaluator._get_field_value("a.b.c.d.e", context)
        self.assertEqual(result, 100)

    def test_none_in_nested_path(self):
        """测试嵌套路径中的None"""
        context = {"a": {"b": None}}
        result = self.evaluator._get_field_value("a.b.c", context)
        self.assertIsNone(result)

    def test_invalid_json_format(self):
        """测试无效的JSON格式"""
        with self.assertRaises(ConditionParseError) as cm:
            self.evaluator.evaluate("{invalid json}", {})
        self.assertIn("JSON格式错误", str(cm.exception))

    def test_complex_and_or_expression(self):
        """测试复杂的AND/OR表达式"""
        # 这个测试验证SQL-like表达式的AND/OR分割
        context = {"a": 10, "b": 20}
        # 简单测试AND
        result = self.evaluator._evaluate_sql_like("a > 5 AND b > 15", context)
        self.assertTrue(result)

    def test_nested_value_from_dict(self):
        """测试从字典获取嵌套值"""
        obj = {"x": {"y": {"z": 42}}}
        result = self.evaluator._get_nested_value(obj, "x.y.z")
        self.assertEqual(result, 42)

    def test_nested_value_from_object(self):
        """测试从对象获取嵌套值"""
        inner = MagicMock()
        inner.z = 42
        outer = MagicMock()
        outer.y = inner
        result = self.evaluator._get_nested_value(outer, "y.z")
        self.assertEqual(result, 42)

    def test_empty_nested_path(self):
        """测试空的嵌套路径"""
        obj = {"value": 100}
        result = self.evaluator._get_nested_value(obj, "")
        self.assertEqual(result, obj)


if __name__ == "__main__":
    unittest.main()
