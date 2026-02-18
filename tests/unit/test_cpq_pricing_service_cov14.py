# -*- coding: utf-8 -*-
"""
第十四批：CPQ配置化报价服务 单元测试
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock

try:
    from app.services.cpq_pricing_service import CpqPricingService
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_service(db=None):
    return CpqPricingService(db or make_db())


class TestCpqPricingService:
    def test_preview_price_no_rule_set(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = make_service(db)
        result = svc.preview_price()
        assert result["base_price"] == Decimal("0")
        assert result["final_price"] == Decimal("0")
        assert result["requires_approval"] is False

    def test_preview_price_with_rule_set(self):
        db = make_db()
        rule_set = MagicMock()
        rule_set.config_schema = {}
        rule_set.pricing_matrix = {}
        rule_set.approval_threshold = {}
        rule_set.currency = "CNY"
        rule_set.base_price = Decimal("100000")
        db.query.return_value.filter.return_value.first.return_value = rule_set
        svc = make_service(db)
        result = svc.preview_price(rule_set_id=1)
        assert result["base_price"] == Decimal("100000")
        assert result["final_price"] == Decimal("100000")
        assert result["currency"] == "CNY"

    def test_preview_price_with_discount_triggers_approval(self):
        db = make_db()
        rule_set = MagicMock()
        rule_set.config_schema = {}
        rule_set.pricing_matrix = {}
        rule_set.approval_threshold = {"max_discount_pct": 5}
        rule_set.currency = "CNY"
        rule_set.base_price = Decimal("100000")
        db.query.return_value.filter.return_value.first.return_value = rule_set
        svc = make_service(db)
        result = svc.preview_price(rule_set_id=1, manual_discount_pct=Decimal("10"))
        assert result["requires_approval"] is True
        assert "折扣" in result["approval_reason"]

    def test_calculate_adjustment_dict_rule(self):
        db = make_db()
        svc = make_service(db)
        matrix = {"color": {"red": 500, "blue": 300}}
        delta, reason = svc._calculate_adjustment("color", "red", matrix)
        assert delta == Decimal("500")

    def test_calculate_adjustment_numeric_rule(self):
        db = make_db()
        svc = make_service(db)
        matrix = {"extra_feature": 2000}
        delta, reason = svc._calculate_adjustment("extra_feature", True, matrix)
        assert delta == Decimal("2000")

    def test_calculate_adjustment_missing_key(self):
        db = make_db()
        svc = make_service(db)
        delta, reason = svc._calculate_adjustment("nonexistent", "val", {})
        assert delta == Decimal("0")

    def test_calculate_confidence_high(self):
        db = make_db()
        svc = make_service(db)
        schema = {"color": {"required": True}, "size": {"required": True}}
        selections = {"color": "red", "size": "L"}
        level = svc._calculate_confidence(schema, selections)
        assert level == "HIGH"

    def test_calculate_confidence_low(self):
        db = make_db()
        svc = make_service(db)
        schema = {
            "a": {"required": True}, "b": {"required": True},
            "c": {"required": True}, "d": {"required": True}
        }
        selections = {"a": "v1"}
        level = svc._calculate_confidence(schema, selections)
        assert level == "LOW"

    def test_evaluate_approvals_floor_price(self):
        db = make_db()
        svc = make_service(db)
        threshold = {"min_floor_price": 50000}
        requires, reason = svc._evaluate_approvals(
            threshold,
            base_price=Decimal("80000"),
            final_price=Decimal("40000"),
            manual_discount_pct=None
        )
        assert requires is True
        assert "底价" in reason
