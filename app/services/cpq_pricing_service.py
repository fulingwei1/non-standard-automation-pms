# -*- coding: utf-8 -*-
"""
CPQ 配置化报价服务
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.sales import CpqRuleSet, QuoteTemplateVersion


class CpqPricingService:
    """CPQ 价格计算服务"""

    def __init__(self, db: Session):
        self.db = db

    def preview_price(
        self,
        *,
        rule_set_id: Optional[int] = None,
        template_version_id: Optional[int] = None,
        selections: Optional[Dict[str, Any]] = None,
        manual_discount_pct: Optional[Decimal] = None,
        manual_markup_pct: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        rule_set = self._resolve_rule_set(rule_set_id, template_version_id)
        config_schema = {}
        pricing_matrix = {}
        approval_threshold = {}
        currency = "CNY"
        base_price = Decimal("0")
        if rule_set:
            config_schema = rule_set.config_schema or {}
            pricing_matrix = rule_set.pricing_matrix or {}
            approval_threshold = rule_set.approval_threshold or {}
            currency = rule_set.currency or "CNY"
            base_price = Decimal(rule_set.base_price or 0)
        elif template_version_id:
            version = self.db.query(QuoteTemplateVersion).filter(QuoteTemplateVersion.id == template_version_id).first()
            if version:
                config_schema = version.config_schema or {}
                pricing_matrix = version.pricing_rules or {}
                currency = "CNY"
                base_price = Decimal(version.pricing_rules.get("base_price", 0)) if version.pricing_rules else Decimal("0")
        selections = selections or {}

        adjustments = []
        adjustment_total = Decimal("0")

        for key, value in selections.items():
            delta, reason = self._calculate_adjustment(key, value, pricing_matrix)
            if delta:
                adjustment_total += delta
                adjustments.append({
                    "key": key,
                    "label": str(value),
                    "value": delta,
                    "reason": reason or f"配置项 {key}",
                })

        if manual_markup_pct:
            markup_value = (base_price + adjustment_total) * manual_markup_pct / Decimal("100")
            if markup_value:
                adjustment_total += markup_value
                adjustments.append({
                    "key": "manual_markup",
                    "label": "附加费用",
                    "value": markup_value,
                    "reason": f"人工加成 {manual_markup_pct}%",
                })

        if manual_discount_pct:
            discount_value = (base_price + adjustment_total) * manual_discount_pct / Decimal("100")
            if discount_value:
                adjustment_total -= discount_value
                adjustments.append({
                    "key": "manual_discount",
                    "label": "手动折扣",
                    "value": -discount_value,
                    "reason": f"人工折扣 {manual_discount_pct}%",
                })

        final_price = base_price + adjustment_total
        requires_approval, approval_reason = self._evaluate_approvals(
            approval_threshold,
            base_price=base_price,
            final_price=final_price,
            manual_discount_pct=manual_discount_pct,
        )

        confidence_level = self._calculate_confidence(config_schema, selections)

        return {
            "base_price": base_price,
            "adjustment_total": adjustment_total,
            "final_price": final_price,
            "currency": currency,
            "adjustments": adjustments,
            "requires_approval": requires_approval,
            "approval_reason": approval_reason,
            "confidence_level": confidence_level,
        }

    def _resolve_rule_set(self, rule_set_id: Optional[int], template_version_id: Optional[int]) -> Optional[CpqRuleSet]:
        if rule_set_id:
            return self.db.query(CpqRuleSet).filter(CpqRuleSet.id == rule_set_id).first()
        if template_version_id:
            version = (
                self.db.query(QuoteTemplateVersion)
                .filter(QuoteTemplateVersion.id == template_version_id)
                .first()
            )
            if version and version.rule_set_id:
                return self.db.query(CpqRuleSet).filter(CpqRuleSet.id == version.rule_set_id).first()
        return None

    def _calculate_adjustment(self, key: str, value: Any, pricing_matrix: Dict[str, Any]) -> Tuple[Decimal, Optional[str]]:
        if not pricing_matrix:
            return Decimal("0"), None
        rules = pricing_matrix.get(key)
        if not rules:
            return Decimal("0"), None

        # 允许数值型或对象型规则
        if isinstance(rules, (int, float, Decimal)):
            return Decimal(rules), None
        if isinstance(rules, dict):
            matched = rules.get(str(value)) or rules.get(value)
            if matched is None:
                # 支持范围或默认逻辑
                default_value = rules.get("default")
                if default_value is not None:
                    return Decimal(default_value), "默认调价"
                return Decimal("0"), None
            if isinstance(matched, dict):
                amount = Decimal(matched.get("amount", 0))
                reason = matched.get("reason")
                return amount, reason
            return Decimal(matched), None
        return Decimal("0"), None

    def _evaluate_approvals(
        self,
        threshold: Dict[str, Any],
        *,
        base_price: Decimal,
        final_price: Decimal,
        manual_discount_pct: Optional[Decimal],
    ) -> (bool, Optional[str]):
        if not threshold:
            return False, None
        max_discount_pct = Decimal(str(threshold.get("max_discount_pct", 0)))
        min_floor = Decimal(str(threshold.get("min_floor_price", 0)))

        if manual_discount_pct and manual_discount_pct > max_discount_pct > 0:
            return True, f"折扣 {manual_discount_pct}% 超过阈值 {max_discount_pct}%"

        if min_floor and final_price < min_floor:
            return True, f"报价低于底价 {min_floor}"

        margin_target = Decimal(str(threshold.get("min_margin_pct", 0)))
        if margin_target and base_price > 0:
            margin_pct = (final_price - base_price) / base_price * Decimal("100")
            if margin_pct < margin_target:
                return True, f"毛利率 {round(margin_pct, 2)}% 低于阈值 {margin_target}%"

        return False, None

    def _calculate_confidence(self, config_schema: Dict[str, Any], selections: Dict[str, Any]) -> str:
        if not config_schema:
            return "MEDIUM"
        required_keys = [key for key, meta in config_schema.items() if isinstance(meta, dict) and meta.get("required")]
        if not required_keys:
            return "HIGH"
        provided = [key for key in required_keys if selections.get(key) is not None]
        ratio = len(provided) / len(required_keys) if required_keys else 1
        if ratio >= 0.8:
            return "HIGH"
        if ratio >= 0.5:
            return "MEDIUM"
        return "LOW"
