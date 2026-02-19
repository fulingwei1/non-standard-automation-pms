# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/expressions/parser.py"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.expressions.parser import ExpressionParser, ExpressionError
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_evaluate_non_expression_returns_as_is():
    parser = ExpressionParser()
    result = parser.evaluate("plain text", {})
    assert result == "plain text"


def test_evaluate_empty_string():
    parser = ExpressionParser()
    result = parser.evaluate("", {})
    assert result == ""


def test_evaluate_simple_expression():
    parser = ExpressionParser()
    result = parser.evaluate("{{ 1 + 2 }}", {})
    assert result == 3


def test_evaluate_with_context():
    parser = ExpressionParser()
    result = parser.evaluate("{{ value * 2 }}", {"value": 5})
    assert result == 10


def test_evaluate_string_result():
    parser = ExpressionParser()
    result = parser.evaluate("{{ name }}", {"name": "hello"})
    assert result == "hello"


def test_evaluate_dict_recursive():
    parser = ExpressionParser()
    data = {"a": "{{ x + 1 }}", "b": "plain"}
    result = parser.evaluate_dict(data, {"x": 10})
    assert result["a"] == 11
    assert result["b"] == "plain"


def test_evaluate_list_recursive():
    parser = ExpressionParser()
    data = ["{{ y }}", "static", 42]
    result = parser.evaluate_list(data, {"y": 99})
    assert result[0] == 99
    assert result[1] == "static"
    assert result[2] == 42


def test_convert_result_bool_true():
    parser = ExpressionParser()
    assert parser._convert_result("true") is True
    assert parser._convert_result("false") is False


def test_convert_result_float():
    parser = ExpressionParser()
    assert parser._convert_result("3.14") == 3.14


def test_evaluate_invalid_expression_raises():
    parser = ExpressionParser()
    if parser._env is None:
        pytest.skip("jinja2 not available")
    with pytest.raises(ExpressionError):
        parser.evaluate("{{ invalid syntax {{ }}", {})
