# -*- coding: utf-8 -*-
"""
approval_engine/condition_parser.py 单元测试（第二批）
"""
import pytest
from unittest.mock import MagicMock


def _make_evaluator():
    from app.services.approval_engine.condition_parser import ConditionEvaluator
    return ConditionEvaluator()


# ─── 1. evaluate - 空表达式 ────────────────────────────────────────────────
def test_evaluate_empty_expression():
    ev = _make_evaluator()
    result = ev.evaluate("", {})
    assert result is None


# ─── 2. _compare_values - 基础操作符 ──────────────────────────────────────
def test_compare_eq():
    ev = _make_evaluator()
    assert ev._compare_values(5, "==", 5) is True
    assert ev._compare_values(5, "==", 6) is False


def test_compare_ne():
    ev = _make_evaluator()
    assert ev._compare_values(5, "!=", 6) is True
    assert ev._compare_values(5, "!=", 5) is False


def test_compare_gt():
    ev = _make_evaluator()
    assert ev._compare_values(10, ">", 5) is True
    assert ev._compare_values(5, ">", 10) is False
    assert ev._compare_values(None, ">", 5) is False


def test_compare_gte():
    ev = _make_evaluator()
    assert ev._compare_values(5, ">=", 5) is True
    assert ev._compare_values(4, ">=", 5) is False


def test_compare_lt():
    ev = _make_evaluator()
    assert ev._compare_values(3, "<", 5) is True
    assert ev._compare_values(5, "<", 3) is False


def test_compare_lte():
    ev = _make_evaluator()
    assert ev._compare_values(5, "<=", 5) is True
    assert ev._compare_values(6, "<=", 5) is False


def test_compare_in():
    ev = _make_evaluator()
    assert ev._compare_values("a", "in", ["a", "b"]) is True
    assert ev._compare_values("c", "in", ["a", "b"]) is False
    assert ev._compare_values("a", "in", None) is False


def test_compare_not_in():
    ev = _make_evaluator()
    assert ev._compare_values("c", "not_in", ["a", "b"]) is True
    assert ev._compare_values("a", "not_in", ["a", "b"]) is False


def test_compare_between():
    ev = _make_evaluator()
    assert ev._compare_values(5, "between", [1, 10]) is True
    assert ev._compare_values(15, "between", [1, 10]) is False
    assert ev._compare_values(None, "between", [1, 10]) is False
    assert ev._compare_values(5, "between", [1]) is False  # 格式错误


def test_compare_contains():
    ev = _make_evaluator()
    assert ev._compare_values("hello world", "contains", "world") is True
    assert ev._compare_values("hello", "contains", "world") is False
    assert ev._compare_values(None, "contains", "world") is False


def test_compare_starts_with():
    ev = _make_evaluator()
    assert ev._compare_values("hello", "starts_with", "he") is True
    assert ev._compare_values("hello", "starts_with", "lo") is False


def test_compare_ends_with():
    ev = _make_evaluator()
    assert ev._compare_values("hello", "ends_with", "lo") is True
    assert ev._compare_values("hello", "ends_with", "he") is False


def test_compare_is_null():
    ev = _make_evaluator()
    assert ev._compare_values(None, "is_null", True) is True
    assert ev._compare_values("val", "is_null", True) is False
    assert ev._compare_values(None, "is_null", False) is False


def test_compare_unknown_op():
    ev = _make_evaluator()
    # 不支持的操作符返回 False
    assert ev._compare_values(5, "UNKNOWN_OP", 5) is False


# ─── 3. _get_field_value - 路径解析 ───────────────────────────────────────
def test_get_field_value_simple():
    ev = _make_evaluator()
    context = {"amount": 100}
    assert ev._get_field_value("amount", context) == 100


def test_get_field_value_nested():
    ev = _make_evaluator()
    context = {"form": {"days": 5}}
    assert ev._get_field_value("form.days", context) == 5


def test_get_field_value_missing():
    ev = _make_evaluator()
    context = {}
    assert ev._get_field_value("nonexistent", context) is None


def test_get_field_value_today():
    from datetime import date
    ev = _make_evaluator()
    result = ev._get_field_value("today()", {})
    assert result == date.today()


def test_get_field_value_user():
    ev = _make_evaluator()
    context = {"user": {"level": "manager"}}
    assert ev._get_field_value("user.level", context) == "manager"


# ─── 4. _evaluate_simple_conditions ──────────────────────────────────────
def test_evaluate_simple_conditions_and_true():
    ev = _make_evaluator()
    conditions = {
        "operator": "AND",
        "items": [
            {"field": "amount", "op": ">", "value": 0},
            {"field": "days", "op": "<=", "value": 10},
        ]
    }
    context = {"amount": 5, "days": 3}
    assert ev._evaluate_simple_conditions(conditions, context) is True


def test_evaluate_simple_conditions_and_false():
    ev = _make_evaluator()
    conditions = {
        "operator": "AND",
        "items": [
            {"field": "amount", "op": ">", "value": 100},
        ]
    }
    context = {"amount": 5}
    assert ev._evaluate_simple_conditions(conditions, context) is False


def test_evaluate_simple_conditions_or():
    ev = _make_evaluator()
    conditions = {
        "operator": "OR",
        "items": [
            {"field": "amount", "op": ">", "value": 100},
            {"field": "days", "op": ">", "value": 1},
        ]
    }
    context = {"amount": 5, "days": 3}
    assert ev._evaluate_simple_conditions(conditions, context) is True


def test_evaluate_simple_conditions_empty():
    ev = _make_evaluator()
    assert ev._evaluate_simple_conditions({}, {}) is True
    assert ev._evaluate_simple_conditions({"operator": "AND", "items": []}, {}) is True


# ─── 5. evaluate - Jinja2 表达式 ─────────────────────────────────────────
def test_evaluate_jinja2_expression():
    ev = _make_evaluator()
    result = ev.evaluate("{{ amount }}", {"amount": 42})
    assert result == 42


def test_evaluate_json_conditions():
    import json
    ev = _make_evaluator()
    cond = json.dumps({"operator": "AND", "items": [{"field": "x", "op": ">", "value": 0}]})
    result = ev.evaluate(cond, {"x": 5})
    assert result is True
