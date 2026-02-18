# -*- coding: utf-8 -*-
"""第五批：approval_engine/condition_parser.py 单元测试"""
import json
import pytest
from unittest.mock import MagicMock

try:
    from app.services.approval_engine.condition_parser import (
        ConditionEvaluator,
        ConditionParseError,
    )
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="condition_parser not importable")


class TestConditionEvaluator:
    def setup_method(self):
        self.ev = ConditionEvaluator()

    def test_empty_expression_returns_none(self):
        result = self.ev.evaluate("", {})
        assert result is None

    def test_json_and_all_pass(self):
        expr = json.dumps({
            "operator": "AND",
            "items": [
                {"field": "amount", "op": ">", "value": 100},
                {"field": "amount", "op": "<", "value": 10000},
            ],
        })
        assert self.ev.evaluate(expr, {"amount": 500}) is True

    def test_json_and_one_fail(self):
        expr = json.dumps({
            "operator": "AND",
            "items": [
                {"field": "amount", "op": ">", "value": 1000},
                {"field": "amount", "op": "<", "value": 10000},
            ],
        })
        assert self.ev.evaluate(expr, {"amount": 500}) is False

    def test_json_or_one_pass(self):
        expr = json.dumps({
            "operator": "OR",
            "items": [
                {"field": "amount", "op": ">", "value": 10000},
                {"field": "status", "op": "==", "value": "URGENT"},
            ],
        })
        assert self.ev.evaluate(expr, {"amount": 500, "status": "URGENT"}) is True

    def test_json_or_none_pass(self):
        expr = json.dumps({
            "operator": "OR",
            "items": [
                {"field": "amount", "op": ">", "value": 10000},
                {"field": "status", "op": "==", "value": "URGENT"},
            ],
        })
        assert self.ev.evaluate(expr, {"amount": 500, "status": "NORMAL"}) is False

    def test_json_empty_items(self):
        expr = json.dumps({"operator": "AND", "items": []})
        assert self.ev.evaluate(expr, {}) is True

    def test_eq_operator(self):
        expr = json.dumps({"operator": "AND", "items": [
            {"field": "level", "op": "==", "value": "HIGH"}
        ]})
        assert self.ev.evaluate(expr, {"level": "HIGH"}) is True
        assert self.ev.evaluate(expr, {"level": "LOW"}) is False

    def test_in_operator(self):
        expr = json.dumps({"operator": "AND", "items": [
            {"field": "status", "op": "in", "value": ["A", "B", "C"]}
        ]})
        assert self.ev.evaluate(expr, {"status": "A"}) is True
        assert self.ev.evaluate(expr, {"status": "Z"}) is False

    def test_between_operator(self):
        expr = json.dumps({"operator": "AND", "items": [
            {"field": "score", "op": "between", "value": [60, 100]}
        ]})
        assert self.ev.evaluate(expr, {"score": 80}) is True
        assert self.ev.evaluate(expr, {"score": 50}) is False

    def test_contains_operator(self):
        expr = json.dumps({"operator": "AND", "items": [
            {"field": "name", "op": "contains", "value": "foo"}
        ]})
        assert self.ev.evaluate(expr, {"name": "foobar"}) is True
        assert self.ev.evaluate(expr, {"name": "baz"}) is False

    def test_invalid_json_raises(self):
        with pytest.raises(ConditionParseError):
            self.ev.evaluate("{invalid json}", {})

    def test_nested_field_path(self):
        expr = json.dumps({"operator": "AND", "items": [
            {"field": "form.days", "op": "<=", "value": 3}
        ]})
        assert self.ev.evaluate(expr, {"form": {"days": 2}}) is True
        assert self.ev.evaluate(expr, {"form": {"days": 5}}) is False
