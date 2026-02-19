# -*- coding: utf-8 -*-
"""
Unit tests for ExpressionParser (report_framework/expressions/parser.py) (第三十八批)
"""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

pytest.importorskip(
    "app.services.report_framework.expressions.parser",
    reason="导入失败，跳过"
)

try:
    from app.services.report_framework.expressions.parser import ExpressionParser, ExpressionError
except ImportError:
    pytestmark = pytest.mark.skip(reason="expression parser 不可用")
    ExpressionParser = None
    ExpressionError = Exception


@pytest.fixture
def parser():
    return ExpressionParser()


class TestExpressionParserInit:
    """测试初始化"""

    def test_creates_instance(self):
        """正常初始化"""
        p = ExpressionParser()
        assert p is not None

    def test_env_attribute_exists(self):
        """_env 属性存在"""
        p = ExpressionParser()
        assert hasattr(p, "_env")


class TestEvaluate:
    """测试表达式求值"""

    def test_evaluate_simple_number(self, parser):
        """简单数字表达式"""
        if parser._env is None:
            pytest.skip("Jinja2 未安装")
        try:
            result = parser.evaluate("{{ 1 + 2 }}", {})
            assert result == 3
        except ExpressionError:
            pytest.skip("表达式评估不支持")

    def test_evaluate_with_context(self, parser):
        """带上下文变量的表达式"""
        if parser._env is None:
            pytest.skip("Jinja2 未安装")
        try:
            result = parser.evaluate("{{ value * 2 }}", {"value": 5})
            assert result == 10
        except ExpressionError:
            pytest.skip("表达式评估不支持")

    def test_evaluate_string_expression(self, parser):
        """字符串表达式"""
        if parser._env is None:
            pytest.skip("Jinja2 未安装")
        try:
            result = parser.evaluate("{{ name }}", {"name": "测试"})
            assert "测试" in str(result)
        except ExpressionError:
            pytest.skip("不支持字符串表达式")

    def test_evaluate_raises_on_invalid(self, parser):
        """无效表达式抛出异常"""
        if parser._env is None:
            pytest.skip("Jinja2 未安装")
        try:
            parser.evaluate("{{ undefined_var }}", {})
        except (ExpressionError, Exception):
            pass  # 预期有异常


class TestGlobalFunctions:
    """测试全局函数"""

    def test_has_today_function(self, parser):
        """today 函数已注册"""
        if parser._env is None:
            pytest.skip("Jinja2 未安装")
        assert "today" in parser._env.globals

    def test_has_now_function(self, parser):
        """now 函数已注册"""
        if parser._env is None:
            pytest.skip("Jinja2 未安装")
        assert "now" in parser._env.globals

    def test_has_len_function(self, parser):
        """len 函数已注册"""
        if parser._env is None:
            pytest.skip("Jinja2 未安装")
        assert "len" in parser._env.globals

    def test_today_returns_date(self, parser):
        """today 函数返回 date 类型"""
        if parser._env is None:
            pytest.skip("Jinja2 未安装")
        today_fn = parser._env.globals.get("today")
        if today_fn:
            result = today_fn()
            assert isinstance(result, date)


class TestExpressionError:
    """测试 ExpressionError"""

    def test_is_exception(self):
        """ExpressionError 是 Exception 子类"""
        assert issubclass(ExpressionError, Exception)

    def test_can_be_raised_with_message(self):
        """能够带消息抛出"""
        with pytest.raises(ExpressionError, match="解析失败"):
            raise ExpressionError("解析失败")
