# -*- coding: utf-8 -*-
"""CpqPricingService 单元测试 - 报价计算逻辑（含税/不含税、折扣率）"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock


class TestCpqPricingService:

    def _make_service(self, rule_set=None, version=None):
        from app.services.cpq_pricing_service import CpqPricingService
        db = MagicMock()
        if rule_set is not None:
            db.query.return_value.filter.return_value.first.return_value = rule_set
        else:
            db.query.return_value.filter.return_value.first.return_value = version
        return CpqPricingService(db), db

    # ---------- preview_price: 基础价格无选项 ----------

    def test_preview_price_no_rule_set(self):
        """无规则集时基础价为0，confidence=MEDIUM"""
        svc, db = self._make_service(rule_set=None, version=None)
        result = svc.preview_price()
        assert result["base_price"] == Decimal("0")
        assert result["final_price"] == Decimal("0")
        assert result["currency"] == "CNY"
        assert result["confidence_level"] == "MEDIUM"
        assert result["adjustments"] == []

    def test_preview_price_with_rule_set(self):
        """有规则集时返回正确基础价格"""
        rule_set = MagicMock()
        rule_set.config_schema = {}
        rule_set.pricing_matrix = {}
        rule_set.approval_threshold = {}
        rule_set.currency = "CNY"
        rule_set.base_price = 10000
        svc, db = self._make_service(rule_set=rule_set)
        result = svc.preview_price(rule_set_id=1)
        assert result["base_price"] == Decimal("10000")
        assert result["final_price"] == Decimal("10000")

    # ---------- 折扣率计算 ----------

    def test_preview_price_manual_discount(self):
        """手动折扣率应正确从最终价格中扣除"""
        rule_set = MagicMock()
        rule_set.config_schema = {}
        rule_set.pricing_matrix = {}
        rule_set.approval_threshold = {}
        rule_set.currency = "CNY"
        rule_set.base_price = 10000
        svc, db = self._make_service(rule_set=rule_set)
        result = svc.preview_price(rule_set_id=1, manual_discount_pct=Decimal("10"))
        # 10000 * 10% = 1000 折扣, final = 9000
        assert result["final_price"] == Decimal("9000")
        discount_adj = [a for a in result["adjustments"] if a["key"] == "manual_discount"]
        assert len(discount_adj) == 1
        assert discount_adj[0]["value"] == Decimal("-1000")

    def test_preview_price_manual_markup(self):
        """手动加成率应正确叠加到最终价格"""
        rule_set = MagicMock()
        rule_set.config_schema = {}
        rule_set.pricing_matrix = {}
        rule_set.approval_threshold = {}
        rule_set.currency = "CNY"
        rule_set.base_price = 10000
        svc, db = self._make_service(rule_set=rule_set)
        result = svc.preview_price(rule_set_id=1, manual_markup_pct=Decimal("5"))
        # 10000 * 5% = 500 加成, final = 10500
        assert result["final_price"] == Decimal("10500")
        markup_adj = [a for a in result["adjustments"] if a["key"] == "manual_markup"]
        assert len(markup_adj) == 1
        assert markup_adj[0]["value"] == Decimal("500")

    # ---------- 审批触发 ----------

    def test_requires_approval_when_discount_exceeds_threshold(self):
        """折扣率超过阈值时 requires_approval=True"""
        rule_set = MagicMock()
        rule_set.config_schema = {}
        rule_set.pricing_matrix = {}
        rule_set.approval_threshold = {"max_discount_pct": 5}
        rule_set.currency = "CNY"
        rule_set.base_price = 10000
        svc, db = self._make_service(rule_set=rule_set)
        result = svc.preview_price(rule_set_id=1, manual_discount_pct=Decimal("10"))
        assert result["requires_approval"] is True
        assert "折扣" in result["approval_reason"]

    def test_no_approval_required_within_threshold(self):
        """折扣率在阈值内时 requires_approval=False"""
        rule_set = MagicMock()
        rule_set.config_schema = {}
        rule_set.pricing_matrix = {}
        rule_set.approval_threshold = {"max_discount_pct": 20}
        rule_set.currency = "CNY"
        rule_set.base_price = 10000
        svc, db = self._make_service(rule_set=rule_set)
        result = svc.preview_price(rule_set_id=1, manual_discount_pct=Decimal("10"))
        assert result["requires_approval"] is False

    # ---------- 置信度计算 ----------

    def test_confidence_high_all_required_provided(self):
        """所有必填项都填写时 confidence=HIGH"""
        svc, db = self._make_service()
        schema = {"size": {"required": True}, "color": {"required": True}}
        selections = {"size": "large", "color": "red"}
        level = svc._calculate_confidence(schema, selections)
        assert level == "HIGH"

    def test_confidence_low_few_required_provided(self):
        """填写比例<50% 时 confidence=LOW"""
        svc, db = self._make_service()
        schema = {
            "a": {"required": True},
            "b": {"required": True},
            "c": {"required": True},
        }
        selections = {"a": "v"}
        level = svc._calculate_confidence(schema, selections)
        assert level == "LOW"

    # ---------- pricing_matrix 调价 ----------

    def test_pricing_matrix_dict_value(self):
        """pricing_matrix 数值型规则直接返回 Decimal"""
        svc, db = self._make_service()
        delta, _ = svc._calculate_adjustment("weight", "heavy", {"weight": 200})
        assert delta == Decimal("200")

    def test_pricing_matrix_matched_dict_with_reason(self):
        """pricing_matrix 字典型规则按 value 匹配并带 reason"""
        svc, db = self._make_service()
        matrix = {"material": {"stainless": {"amount": 500, "reason": "不锈钢附加"}}}
        delta, reason = svc._calculate_adjustment("material", "stainless", matrix)
        assert delta == Decimal("500")
        assert reason == "不锈钢附加"

    def test_pricing_matrix_default_fallback(self):
        """pricing_matrix 无匹配时使用 default 值"""
        svc, db = self._make_service()
        matrix = {"finish": {"glossy": 100, "default": 50}}
        delta, reason = svc._calculate_adjustment("finish", "matte", matrix)
        assert delta == Decimal("50")
        assert reason == "默认调价"

    # ---------- _evaluate_approvals: 底价保护 ----------

    def test_floor_price_triggers_approval(self):
        """最终价低于底价时触发审批"""
        svc, db = self._make_service()
        threshold = {"min_floor_price": 8000}
        flag, reason = svc._evaluate_approvals(
            threshold,
            base_price=Decimal("10000"),
            final_price=Decimal("7000"),
            manual_discount_pct=None,
        )
        assert flag is True
        assert "底价" in reason

    def test_no_threshold_no_approval(self):
        """无阈值配置时不触发审批"""
        svc, db = self._make_service()
        flag, reason = svc._evaluate_approvals(
            {},
            base_price=Decimal("10000"),
            final_price=Decimal("9000"),
            manual_discount_pct=None,
        )
        assert flag is False
        assert reason is None
