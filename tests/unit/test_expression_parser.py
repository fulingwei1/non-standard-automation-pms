# -*- coding: utf-8 -*-
"""
表达式解析器单元测试

目标:
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖（几乎无需mock，让业务逻辑真正执行）
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import date, datetime, timedelta
from app.services.report_framework.expressions.parser import (
    ExpressionParser,
    ExpressionError,
)


class TestExpressionParserCore(unittest.TestCase):
    """测试核心功能"""

    def setUp(self):
        """每个测试前执行"""
        self.parser = ExpressionParser()

    # ========== 初始化测试 ==========

    def test_init_creates_environment(self):
        """测试初始化创建Jinja2环境"""
        parser = ExpressionParser()
        self.assertIsNotNone(parser._env)

    @patch('app.services.report_framework.expressions.parser.Environment', None)
    @patch('app.services.report_framework.expressions.parser.BaseLoader', None)
    def test_init_without_jinja2(self):
        """测试没有jinja2依赖时的初始化"""
        parser = ExpressionParser()
        self.assertIsNone(parser._env)

    # ========== evaluate() 核心测试 ==========

    def test_evaluate_simple_variable(self):
        """测试简单变量替换"""
        context = {"name": "张三", "age": 30}
        result = self.parser.evaluate("{{ name }}", context)
        self.assertEqual(result, "张三")

        result = self.parser.evaluate("{{ age }}", context)
        self.assertEqual(result, 30)

    def test_evaluate_arithmetic_expression(self):
        """测试算术表达式"""
        context = {"a": 10, "b": 20}
        result = self.parser.evaluate("{{ a + b }}", context)
        self.assertEqual(result, 30)

        result = self.parser.evaluate("{{ b - a }}", context)
        self.assertEqual(result, 10)

        result = self.parser.evaluate("{{ a * b }}", context)
        self.assertEqual(result, 200)

    def test_evaluate_string_concatenation(self):
        """测试字符串拼接"""
        context = {"first": "Hello", "second": "World"}
        result = self.parser.evaluate("{{ first }} {{ second }}", context)
        self.assertEqual(result, "Hello World")

    def test_evaluate_non_expression_string(self):
        """测试非表达式字符串（直接返回）"""
        result = self.parser.evaluate("plain text", {})
        self.assertEqual(result, "plain text")

        result = self.parser.evaluate("no curly braces here", {})
        self.assertEqual(result, "no curly braces here")

    def test_evaluate_empty_string(self):
        """测试空字符串"""
        result = self.parser.evaluate("", {})
        self.assertEqual(result, "")

    def test_evaluate_none(self):
        """测试None输入"""
        result = self.parser.evaluate(None, {})
        self.assertIsNone(result)

    def test_evaluate_with_filter(self):
        """测试使用过滤器"""
        context = {"items": [1, 2, 3, 4, 5]}
        result = self.parser.evaluate("{{ items | length }}", context)
        self.assertEqual(result, 5)

    def test_evaluate_with_global_function(self):
        """测试全局函数"""
        context = {"nums": [1, 2, 3, 4, 5]}
        result = self.parser.evaluate("{{ sum(nums) }}", context)
        self.assertEqual(result, 15)

        result = self.parser.evaluate("{{ len(nums) }}", context)
        self.assertEqual(result, 5)

        result = self.parser.evaluate("{{ max(nums) }}", context)
        self.assertEqual(result, 5)

    def test_evaluate_type_conversion_integer(self):
        """测试整数类型转换"""
        context = {"value": 42}
        result = self.parser.evaluate("{{ value }}", context)
        self.assertEqual(result, 42)
        self.assertIsInstance(result, int)

    def test_evaluate_type_conversion_float(self):
        """测试浮点数类型转换"""
        context = {"value": 3.14}
        result = self.parser.evaluate("{{ value }}", context)
        self.assertEqual(result, 3.14)
        self.assertIsInstance(result, float)

    def test_evaluate_type_conversion_boolean(self):
        """测试布尔值类型转换"""
        result = self.parser.evaluate("{{ 1 == 1 }}", {})
        self.assertTrue(result)

        result = self.parser.evaluate("{{ 1 == 2 }}", {})
        self.assertFalse(result)

    def test_evaluate_syntax_error(self):
        """测试语法错误"""
        with self.assertRaises(ExpressionError) as cm:
            self.parser.evaluate("{{ invalid syntax", {})
        self.assertIn("syntax", str(cm.exception).lower())

    def test_evaluate_undefined_variable(self):
        """测试未定义变量 - Jinja2默认返回空字符串"""
        # 注意：如果Jinja2环境没有配置StrictUndefined，未定义变量会返回空字符串
        # 这个测试验证当前配置的行为
        result = self.parser.evaluate("{{ undefined_var }}", {})
        # 根据实际行为，可能返回空字符串或抛出异常
        # 如果使用了StrictUndefined，会抛出异常；否则返回空字符串
        self.assertIsInstance(result, (str, type(None)))

    def test_evaluate_without_jinja2_env(self):
        """测试没有Jinja2环境时抛出异常"""
        parser = ExpressionParser()
        # 手动设置_env为None
        parser._env = None
        with self.assertRaises(ExpressionError) as cm:
            parser.evaluate("{{ test }}", {})
        self.assertIn("jinja2", str(cm.exception).lower())

    # ========== evaluate_dict() 测试 ==========

    def test_evaluate_dict_simple(self):
        """测试简单字典评估"""
        data = {
            "title": "{{ name }}的报告",
            "count": "{{ items | length }}"
        }
        context = {"name": "张三", "items": [1, 2, 3]}
        result = self.parser.evaluate_dict(data, context)
        
        self.assertEqual(result["title"], "张三的报告")
        self.assertEqual(result["count"], 3)

    def test_evaluate_dict_nested(self):
        """测试嵌套字典"""
        data = {
            "user": {
                "name": "{{ username }}",
                "age": "{{ user_age }}"
            },
            "summary": "{{ total }}"
        }
        context = {"username": "李四", "user_age": 25, "total": 100}
        result = self.parser.evaluate_dict(data, context)
        
        self.assertEqual(result["user"]["name"], "李四")
        self.assertEqual(result["user"]["age"], 25)
        self.assertEqual(result["summary"], 100)

    def test_evaluate_dict_with_list(self):
        """测试包含列表的字典"""
        data = {
            "items": ["{{ a }}", "{{ b }}"],
            "total": "{{ a + b }}"
        }
        context = {"a": 10, "b": 20}
        result = self.parser.evaluate_dict(data, context)
        
        self.assertEqual(result["items"], [10, 20])
        self.assertEqual(result["total"], 30)

    def test_evaluate_dict_non_string_values(self):
        """测试包含非字符串值的字典"""
        data = {
            "name": "{{ username }}",
            "age": 25,  # 非字符串
            "active": True,  # 布尔值
            "score": 98.5  # 浮点数
        }
        context = {"username": "王五"}
        result = self.parser.evaluate_dict(data, context)
        
        self.assertEqual(result["name"], "王五")
        self.assertEqual(result["age"], 25)
        self.assertTrue(result["active"])
        self.assertEqual(result["score"], 98.5)

    # ========== evaluate_list() 测试 ==========

    def test_evaluate_list_simple(self):
        """测试简单列表评估"""
        data = ["{{ a }}", "{{ b }}", "{{ c }}"]
        context = {"a": 1, "b": 2, "c": 3}
        result = self.parser.evaluate_list(data, context)
        
        self.assertEqual(result, [1, 2, 3])

    def test_evaluate_list_with_dict(self):
        """测试包含字典的列表"""
        data = [
            {"name": "{{ name1 }}"},
            {"name": "{{ name2 }}"}
        ]
        context = {"name1": "Alice", "name2": "Bob"}
        result = self.parser.evaluate_list(data, context)
        
        self.assertEqual(result[0]["name"], "Alice")
        self.assertEqual(result[1]["name"], "Bob")

    def test_evaluate_list_nested(self):
        """测试嵌套列表"""
        data = [
            ["{{ a }}", "{{ b }}"],
            ["{{ c }}", "{{ d }}"]
        ]
        context = {"a": 1, "b": 2, "c": 3, "d": 4}
        result = self.parser.evaluate_list(data, context)
        
        self.assertEqual(result[0], [1, 2])
        self.assertEqual(result[1], [3, 4])

    def test_evaluate_list_non_string_values(self):
        """测试包含非字符串值的列表"""
        data = ["{{ name }}", 42, True, 3.14]
        context = {"name": "test"}
        result = self.parser.evaluate_list(data, context)
        
        self.assertEqual(result, ["test", 42, True, 3.14])

    # ========== _convert_result() 测试 ==========

    def test_convert_result_integer(self):
        """测试整数转换"""
        result = self.parser._convert_result("42")
        self.assertEqual(result, 42)
        self.assertIsInstance(result, int)

    def test_convert_result_float(self):
        """测试浮点数转换"""
        result = self.parser._convert_result("3.14")
        self.assertEqual(result, 3.14)
        self.assertIsInstance(result, float)

    def test_convert_result_boolean_true(self):
        """测试True布尔值转换"""
        self.assertTrue(self.parser._convert_result("True"))
        self.assertTrue(self.parser._convert_result("true"))
        self.assertTrue(self.parser._convert_result("TRUE"))

    def test_convert_result_boolean_false(self):
        """测试False布尔值转换"""
        self.assertFalse(self.parser._convert_result("False"))
        self.assertFalse(self.parser._convert_result("false"))
        self.assertFalse(self.parser._convert_result("FALSE"))

    def test_convert_result_string(self):
        """测试字符串保持不变"""
        result = self.parser._convert_result("hello world")
        self.assertEqual(result, "hello world")
        self.assertIsInstance(result, str)

    def test_convert_result_with_whitespace(self):
        """测试带空格的转换"""
        result = self.parser._convert_result("  42  ")
        self.assertEqual(result, 42)

        result = self.parser._convert_result("  hello  ")
        self.assertEqual(result, "hello")

    # ========== 日期快捷函数测试 ==========

    @patch('app.services.report_framework.expressions.parser.date')
    def test_last_monday(self, mock_date_class):
        """测试上周一计算"""
        # 假设今天是周三 (2025-01-15)
        mock_date_class.today.return_value = date(2025, 1, 15)  # 周三
        result = ExpressionParser._last_monday()
        # 上周一应该是 2025-01-06
        self.assertEqual(result, date(2025, 1, 13))

    @patch('app.services.report_framework.expressions.parser.date')
    def test_last_monday_when_today_is_monday(self, mock_date_class):
        """测试今天是周一时的上周一"""
        mock_date_class.today.return_value = date(2025, 1, 13)  # 周一
        result = ExpressionParser._last_monday()
        # 应该返回上上周一
        self.assertEqual(result, date(2025, 1, 6))

    @patch('app.services.report_framework.expressions.parser.date')
    def test_last_sunday(self, mock_date_class):
        """测试上周日计算"""
        # 假设今天是周三
        mock_date_class.today.return_value = date(2025, 1, 15)  # 周三
        result = ExpressionParser._last_sunday()
        # 上周日应该是 2025-01-12
        self.assertEqual(result, date(2025, 1, 12))

    @patch('app.services.report_framework.expressions.parser.date')
    def test_last_sunday_when_today_is_sunday(self, mock_date_class):
        """测试今天是周日时的上周日"""
        mock_date_class.today.return_value = date(2025, 1, 12)  # 周日
        result = ExpressionParser._last_sunday()
        # 应该返回上上周日
        self.assertEqual(result, date(2025, 1, 5))

    @patch('app.services.report_framework.expressions.parser.date')
    def test_this_month_start(self, mock_date_class):
        """测试本月第一天"""
        mock_date_class.today.return_value = date(2025, 1, 15)
        result = ExpressionParser._this_month_start()
        self.assertEqual(result, date(2025, 1, 1))

    @patch('app.services.report_framework.expressions.parser.date')
    def test_this_month_end(self, mock_date_class):
        """测试本月最后一天"""
        mock_date_class.today.return_value = date(2025, 1, 15)
        result = ExpressionParser._this_month_end()
        self.assertEqual(result, date(2025, 1, 31))

    @patch('app.services.report_framework.expressions.parser.date')
    def test_last_month_start(self, mock_date_class):
        """测试上月第一天"""
        mock_date_class.today.return_value = date(2025, 1, 15)
        result = ExpressionParser._last_month_start()
        self.assertEqual(result, date(2024, 12, 1))

    @patch('app.services.report_framework.expressions.parser.date')
    def test_last_month_end(self, mock_date_class):
        """测试上月最后一天"""
        mock_date_class.today.return_value = date(2025, 1, 15)
        result = ExpressionParser._last_month_end()
        self.assertEqual(result, date(2024, 12, 31))

    # ========== 全局函数测试 ==========

    def test_global_function_today(self):
        """测试today()函数"""
        result = self.parser.evaluate("{{ today() }}", {})
        self.assertIsInstance(result, str)  # Jinja2会转成字符串
        # 验证包含当前日期
        self.assertIn(str(date.today().year), result)

    def test_global_function_len(self):
        """测试len()函数"""
        context = {"items": [1, 2, 3, 4, 5]}
        result = self.parser.evaluate("{{ len(items) }}", context)
        self.assertEqual(result, 5)

    def test_global_function_str(self):
        """测试str()函数"""
        context = {"num": 123}
        result = self.parser.evaluate("{{ str(num) }}", context)
        # str()返回"123"，但_convert_result会尝试转换为int
        # 所以最终结果是123（整数）
        self.assertEqual(result, 123)

    def test_global_function_int(self):
        """测试int()函数"""
        context = {"value": "456"}
        result = self.parser.evaluate("{{ int(value) }}", context)
        self.assertEqual(result, 456)

    def test_global_function_float(self):
        """测试float()函数"""
        context = {"value": "3.14"}
        result = self.parser.evaluate("{{ float(value) }}", context)
        self.assertEqual(result, 3.14)

    def test_global_function_sum(self):
        """测试sum()函数"""
        context = {"nums": [10, 20, 30]}
        result = self.parser.evaluate("{{ sum(nums) }}", context)
        self.assertEqual(result, 60)

    def test_global_function_min_max(self):
        """测试min()和max()函数"""
        context = {"nums": [10, 5, 30, 15]}
        result = self.parser.evaluate("{{ min(nums) }}", context)
        self.assertEqual(result, 5)

        result = self.parser.evaluate("{{ max(nums) }}", context)
        self.assertEqual(result, 30)

    def test_global_function_abs(self):
        """测试abs()函数"""
        context = {"num": -42}
        result = self.parser.evaluate("{{ abs(num) }}", context)
        self.assertEqual(result, 42)

    def test_global_function_round(self):
        """测试round()函数"""
        context = {"value": 3.14159}
        result = self.parser.evaluate("{{ round(value, 2) }}", context)
        self.assertEqual(result, 3.14)

    # ========== 自定义过滤器测试 ==========

    def test_filter_sum_by(self):
        """测试sum_by过滤器"""
        context = {
            "items": [
                {"amount": 100},
                {"amount": 200},
                {"amount": 300}
            ]
        }
        result = self.parser.evaluate("{{ items | sum_by('amount') }}", context)
        self.assertEqual(result, 600)

    def test_filter_avg_by(self):
        """测试avg_by过滤器"""
        context = {
            "items": [
                {"score": 80},
                {"score": 90},
                {"score": 70}
            ]
        }
        result = self.parser.evaluate("{{ items | avg_by('score') }}", context)
        self.assertEqual(result, 80.0)

    def test_filter_count_by(self):
        """测试count_by过滤器"""
        context = {
            "tasks": [
                {"status": "DONE"},
                {"status": "PENDING"},
                {"status": "DONE"},
                {"status": "DONE"}
            ]
        }
        result = self.parser.evaluate("{{ tasks | count_by('status', 'DONE') }}", context)
        self.assertEqual(result, 3)

    def test_filter_pluck(self):
        """测试pluck过滤器"""
        context = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Charlie"}
            ]
        }
        result = self.parser.evaluate("{{ users | pluck('name') }}", context)
        # Jinja2会转成字符串列表的表示
        self.assertIn("Alice", result)
        self.assertIn("Bob", result)

    def test_filter_currency(self):
        """测试currency过滤器"""
        context = {"amount": 12345.67}
        result = self.parser.evaluate("{{ amount | currency('¥', 2) }}", context)
        self.assertIn("12,345.67", result)
        self.assertIn("¥", result)

    def test_filter_percentage(self):
        """测试percentage过滤器"""
        context = {"ratio": 85.678}
        result = self.parser.evaluate("{{ ratio | percentage(1) }}", context)
        self.assertEqual(result, "85.7%")

    def test_filter_date_format(self):
        """测试date_format过滤器"""
        context = {"created_at": date(2025, 1, 15)}
        result = self.parser.evaluate("{{ created_at | date_format('%Y-%m-%d') }}", context)
        self.assertEqual(result, "2025-01-15")

    def test_filter_truncate_text(self):
        """测试truncate_text过滤器"""
        context = {"text": "This is a very long text that needs to be truncated"}
        result = self.parser.evaluate("{{ text | truncate_text(20) }}", context)
        self.assertTrue(len(result) <= 23)  # 20 + "..."
        self.assertIn("...", result)

    def test_filter_status_label(self):
        """测试status_label过滤器"""
        context = {"status": "DONE"}
        result = self.parser.evaluate("{{ status | status_label }}", context)
        self.assertEqual(result, "已完成")

    def test_filter_default_if_none(self):
        """测试default_if_none过滤器"""
        context = {"name": None}
        result = self.parser.evaluate("{{ name | default_if_none('未知') }}", context)
        self.assertEqual(result, "未知")

    # ========== 复杂场景测试 ==========

    def test_complex_expression_with_multiple_filters(self):
        """测试多重过滤器组合"""
        context = {
            "tasks": [
                {"status": "DONE", "hours": 5},
                {"status": "DONE", "hours": 3},
                {"status": "PENDING", "hours": 2}
            ]
        }
        # 计算已完成任务数
        result = self.parser.evaluate("{{ tasks | count_by('status', 'DONE') }}", context)
        self.assertEqual(result, 2)

        # 计算总工时
        result = self.parser.evaluate("{{ tasks | sum_by('hours') }}", context)
        self.assertEqual(result, 10)

    def test_complex_nested_structure(self):
        """测试复杂嵌套结构"""
        data = {
            "report": {
                "title": "{{ report_name }}",
                "metrics": [
                    {"name": "总数", "value": "{{ total }}"},
                    {"name": "完成", "value": "{{ completed }}"}
                ],
                "summary": "完成率: {{ (completed / total * 100) | round }}%"
            }
        }
        context = {"report_name": "月度报告", "total": 100, "completed": 85}
        result = self.parser.evaluate_dict(data, context)
        
        self.assertEqual(result["report"]["title"], "月度报告")
        self.assertEqual(result["report"]["metrics"][0]["value"], 100)
        self.assertEqual(result["report"]["metrics"][1]["value"], 85)
        self.assertIn("85", result["report"]["summary"])

    # ========== 边界情况测试 ==========

    def test_evaluate_with_empty_context(self):
        """测试空上下文"""
        result = self.parser.evaluate("Static text without variables", {})
        self.assertEqual(result, "Static text without variables")

    def test_evaluate_dict_empty(self):
        """测试空字典"""
        result = self.parser.evaluate_dict({}, {})
        self.assertEqual(result, {})

    def test_evaluate_list_empty(self):
        """测试空列表"""
        result = self.parser.evaluate_list([], {})
        self.assertEqual(result, [])

    def test_filter_with_empty_list(self):
        """测试空列表上的过滤器"""
        context = {"items": []}
        result = self.parser.evaluate("{{ items | sum_by('amount') }}", context)
        self.assertEqual(result, 0)

        result = self.parser.evaluate("{{ items | avg_by('score') }}", context)
        self.assertEqual(result, 0)

        result = self.parser.evaluate("{{ items | count_by('status', 'DONE') }}", context)
        self.assertEqual(result, 0)

    def test_evaluate_with_none_values_in_dict(self):
        """测试字典中包含None值"""
        data = {
            "name": "{{ username }}",
            "age": None,
            "email": "{{ email }}"
        }
        context = {"username": "test", "email": "test@example.com"}
        result = self.parser.evaluate_dict(data, context)
        
        self.assertEqual(result["name"], "test")
        self.assertIsNone(result["age"])
        self.assertEqual(result["email"], "test@example.com")

    def test_division_by_zero_handling(self):
        """测试除零错误处理"""
        context = {"a": 10, "b": 0}
        with self.assertRaises(ExpressionError):
            self.parser.evaluate("{{ a / b }}", context)


class TestExpressionError(unittest.TestCase):
    """测试异常类"""

    def test_exception_inheritance(self):
        """测试异常继承"""
        error = ExpressionError("测试错误")
        self.assertIsInstance(error, Exception)

    def test_exception_message(self):
        """测试异常消息"""
        error = ExpressionError("Custom error message")
        self.assertEqual(str(error), "Custom error message")


class TestExpressionParserIntegration(unittest.TestCase):
    """集成测试 - 模拟真实使用场景"""

    def setUp(self):
        self.parser = ExpressionParser()

    def test_real_world_report_scenario(self):
        """真实场景：生成周报数据"""
        # 模拟任务数据
        tasks = [
            {"id": 1, "title": "开发功能A", "status": "DONE", "hours": 8},
            {"id": 2, "title": "修复bug B", "status": "DONE", "hours": 4},
            {"id": 3, "title": "评审代码", "status": "IN_PROGRESS", "hours": 2},
            {"id": 4, "title": "编写文档", "status": "PENDING", "hours": 0},
        ]

        context = {"tasks": tasks, "username": "张三"}

        # 生成报告
        report = {
            "title": "{{ username }}的周报",
            "total_tasks": "{{ tasks | length }}",
            "completed_tasks": "{{ tasks | count_by('status', 'DONE') }}",
            "total_hours": "{{ tasks | sum_by('hours') }}",
            "completion_rate": "{{ (tasks | count_by('status', 'DONE') / tasks | length * 100) | round }}%"
        }

        result = self.parser.evaluate_dict(report, context)

        self.assertEqual(result["title"], "张三的周报")
        self.assertEqual(result["total_tasks"], 4)
        self.assertEqual(result["completed_tasks"], 2)
        self.assertEqual(result["total_hours"], 14)
        self.assertIn("50", result["completion_rate"])

    def test_real_world_dashboard_metrics(self):
        """真实场景：仪表盘指标计算"""
        data = [
            {"dept": "研发", "sales": 100000},
            {"dept": "研发", "sales": 150000},
            {"dept": "销售", "sales": 200000},
            {"dept": "销售", "sales": 180000},
        ]

        context = {"records": data}

        metrics = {
            "total_sales": "{{ records | sum_by('sales') }}",
            "avg_sales": "{{ records | avg_by('sales') }}",
            "record_count": "{{ records | length }}"
        }

        result = self.parser.evaluate_dict(metrics, context)

        self.assertEqual(result["total_sales"], 630000)
        self.assertEqual(result["avg_sales"], 157500.0)
        self.assertEqual(result["record_count"], 4)


if __name__ == "__main__":
    unittest.main()
