# -*- coding: utf-8 -*-
"""CPQ 定价服务深度测试"""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.services.presale.cpq_pricing_service import CpqPricingService


class FakeQuery:
    def __init__(self, *, first_value=None):
        self.first_value = first_value

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.first_value


class TestCpqPricingServiceDeep:
    def test_resolve_rule_set_by_rule_set_id(self):
        rule_set = SimpleNamespace(id=7)
        db = Mock()
        db.query.return_value = FakeQuery(first_value=rule_set)
        service = CpqPricingService(db)

        result = service._resolve_rule_set(rule_set_id=7, template_version_id=None)

        assert result is rule_set

    def test_resolve_rule_set_by_template_version_rule_set_id(self):
        version = SimpleNamespace(id=2, rule_set_id=9)
        rule_set = SimpleNamespace(id=9)
        db = Mock()
        db.query.side_effect = [FakeQuery(first_value=version), FakeQuery(first_value=rule_set)]
        service = CpqPricingService(db)

        result = service._resolve_rule_set(rule_set_id=None, template_version_id=2)

        assert result is rule_set

    def test_resolve_rule_set_returns_none_when_version_has_no_rule_set(self):
        version = SimpleNamespace(id=2, rule_set_id=None)
        db = Mock()
        db.query.return_value = FakeQuery(first_value=version)
        service = CpqPricingService(db)

        result = service._resolve_rule_set(rule_set_id=None, template_version_id=2)

        assert result is None

    def test_calculate_adjustment_returns_zero_for_empty_matrix(self):
        service = CpqPricingService(Mock())

        delta, reason = service._calculate_adjustment("material", "steel", {})

        assert delta == Decimal("0")
        assert reason is None

    def test_calculate_adjustment_with_numeric_rule(self):
        service = CpqPricingService(Mock())

        delta, reason = service._calculate_adjustment("urgent", True, {"urgent": 200})

        assert delta == Decimal("200")
        assert reason is None

    def test_calculate_adjustment_uses_default_when_no_match(self):
        service = CpqPricingService(Mock())

        delta, reason = service._calculate_adjustment(
            "finish", "matte", {"finish": {"glossy": 100, "default": 50}}
        )

        assert delta == Decimal("50")
        assert reason == "默认调价"

    def test_calculate_adjustment_matches_direct_value_key(self):
        service = CpqPricingService(Mock())

        delta, reason = service._calculate_adjustment(
            "level", 2, {"level": {2: {"amount": 300, "reason": "二级配置"}}}
        )

        assert delta == Decimal("300")
        assert reason == "二级配置"

    def test_evaluate_approvals_triggers_margin_threshold(self):
        service = CpqPricingService(Mock())

        flag, reason = service._evaluate_approvals(
            {"min_margin_pct": 20},
            base_price=Decimal("1000"),
            final_price=Decimal("1100"),
            manual_discount_pct=None,
        )

        assert flag is True
        assert "毛利率" in reason

    def test_calculate_confidence_returns_high_without_required_fields(self):
        service = CpqPricingService(Mock())

        level = service._calculate_confidence({"size": {"required": False}}, {"size": "L"})

        assert level == "HIGH"

    def test_calculate_confidence_returns_medium_for_half_required_fields(self):
        service = CpqPricingService(Mock())

        level = service._calculate_confidence(
            {"a": {"required": True}, "b": {"required": True}}, {"a": 1}
        )

        assert level == "MEDIUM"

    def test_preview_price_uses_template_version_fallback(self):
        version = SimpleNamespace(
            id=5,
            rule_set_id=None,
            config_schema={"size": {"required": True}},
            pricing_rules={"base_price": 2000, "size": {"XL": 300}},
        )
        db = Mock()
        db.query.side_effect = [FakeQuery(first_value=version), FakeQuery(first_value=version)]
        service = CpqPricingService(db)

        result = service.preview_price(template_version_id=5, selections={"size": "XL"})

        assert result["base_price"] == Decimal("2000")
        assert result["adjustment_total"] == Decimal("300")
        assert result["final_price"] == Decimal("2300")
        assert result["currency"] == "CNY"
        assert result["confidence_level"] == "HIGH"
        assert result["requires_approval"] is False

    def test_preview_price_applies_markup_discount_and_approval(self):
        rule_set = SimpleNamespace(
            config_schema={"region": {"required": True}, "tier": {"required": True}},
            pricing_matrix={
                "region": {"CN": {"amount": 100, "reason": "地区加价"}},
                "tier": {"premium": 400},
            },
            approval_threshold={"max_discount_pct": 5},
            currency="USD",
            base_price=1000,
        )
        db = Mock()
        db.query.return_value = FakeQuery(first_value=rule_set)
        service = CpqPricingService(db)

        result = service.preview_price(
            rule_set_id=1,
            selections={"region": "CN", "tier": "premium"},
            manual_markup_pct=Decimal("10"),
            manual_discount_pct=Decimal("8"),
        )

        assert result["currency"] == "USD"
        assert result["base_price"] == Decimal("1000")
        assert len(result["adjustments"]) == 4
        assert result["final_price"] == Decimal("1518")
        assert result["requires_approval"] is True
        assert "折扣" in result["approval_reason"]
        assert result["confidence_level"] == "HIGH"

    def test_preview_price_ignores_zero_adjustments(self):
        rule_set = SimpleNamespace(
            config_schema={},
            pricing_matrix={"feature": {"none": 0}},
            approval_threshold={},
            currency=None,
            base_price=0,
        )
        db = Mock()
        db.query.return_value = FakeQuery(first_value=rule_set)
        service = CpqPricingService(db)

        result = service.preview_price(rule_set_id=1, selections={"feature": "none"})

        assert result["adjustments"] == []
        assert result["final_price"] == Decimal("0")
        assert result["confidence_level"] == "MEDIUM"
