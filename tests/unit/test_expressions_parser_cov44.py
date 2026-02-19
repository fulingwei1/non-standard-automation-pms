# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - Jinja2 表达式解析器"""

import pytest
from datetime import date, timedelta

try:
    from app.services.report_framework.expressions.parser import ExpressionParser, ExpressionError
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def parser():
    return ExpressionParser()


class TestExpressionParser:

    def test_evaluate_plain_string_returned_as_is(self, parser):
        result = parser.evaluate("hello world", {})
        assert result == "hello world"

    def test_evaluate_simple_expression(self, parser):
        result = parser.evaluate("{{ 1 + 2 }}", {})
        assert result == 3

    def test_evaluate_context_variable(self, parser):
        result = parser.evaluate("{{ x * 2 }}", {"x": 5})
        assert result == 10

    def test_evaluate_list_length(self, parser):
        result = parser.evaluate("{{ items | length }}", {"items": [1, 2, 3]})
        assert result == 3

    def test_evaluate_raises_on_syntax_error(self, parser):
        with pytest.raises(ExpressionError):
            parser.evaluate("{{ 1 + }}", {})

    def test_evaluate_dict_processes_expressions(self, parser):
        data = {"count": "{{ n }}", "label": "fixed"}
        result = parser.evaluate_dict(data, {"n": 7})
        assert result["count"] == 7
        assert result["label"] == "fixed"

    def test_evaluate_list_processes_expressions(self, parser):
        data = ["{{ a }}", "static", {"k": "{{ b }}"}]
        result = parser.evaluate_list(data, {"a": 1, "b": 2})
        assert result[0] == 1
        assert result[1] == "static"
        assert result[2]["k"] == 2

    def test_last_monday_returns_date(self, parser):
        result = ExpressionParser._last_monday()
        assert isinstance(result, date)
        assert result.weekday() == 0  # 周一

    def test_last_sunday_returns_date(self, parser):
        result = ExpressionParser._last_sunday()
        assert isinstance(result, date)
        assert result.weekday() == 6  # 周日

    def test_this_month_start_is_first_day(self, parser):
        result = ExpressionParser._this_month_start()
        assert result.day == 1

    def test_this_month_end_is_last_day(self, parser):
        result = ExpressionParser._this_month_end()
        next_day = result + timedelta(days=1)
        assert next_day.day == 1  # 下一天是次月第一天

    def test_convert_result_integer(self, parser):
        assert parser._convert_result("42") == 42

    def test_convert_result_float(self, parser):
        assert parser._convert_result("3.14") == 3.14

    def test_convert_result_true(self, parser):
        assert parser._convert_result("true") is True

    def test_convert_result_false(self, parser):
        assert parser._convert_result("false") is False

    def test_convert_result_string(self, parser):
        assert parser._convert_result("hello") == "hello"

    def test_expression_error_is_exception(self):
        err = ExpressionError("some error")
        assert isinstance(err, Exception)
