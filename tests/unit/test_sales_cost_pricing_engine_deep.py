# -*- coding: utf-8 -*-
"""sales.cost.pricing_engine 深度测试"""

from decimal import Decimal

from app.services.sales.cost.pricing_engine import PricingEngine


class TestSalesCostPricingEngineDeep:
    def test_generate_recommendations_and_competition_adjustment(self):
        engine = PricingEngine()

        rec = engine.generate_recommendations(Decimal("70"), Decimal("0.30"))
        low_comp = engine.adjust_for_competition(rec, "low")
        high_comp = engine.adjust_for_competition(rec, "high")
        default_comp = engine.adjust_for_competition(rec, "weird")

        assert rec.suggested_price == Decimal("100")
        assert rec.low == Decimal("90.00")
        assert rec.medium == Decimal("100")
        assert rec.high == Decimal("115.00")
        assert rec.target_margin_rate == Decimal("30.00")
        assert "行业标准毛利率" in rec.market_analysis

        assert low_comp.medium == Decimal("105.00")
        assert high_comp.medium == Decimal("95.00")
        assert default_comp.medium == rec.medium

    def test_analyze_sensitivity_and_internal_strategy(self):
        engine = PricingEngine()
        rec = engine.generate_recommendations(Decimal("70"), Decimal("0.30"))

        analysis = engine.analyze_sensitivity(Decimal("70"), rec, Decimal("120"))
        no_budget = engine.analyze_sensitivity(Decimal("70"), rec, None)

        assert analysis["cost_base"] == 70.0
        assert analysis["price_range"] == {"min": 90.0, "recommended": 100.0, "max": 115.0}
        assert round(analysis["margin_analysis"]["low_price_margin"], 4) == round((90 - 70) / 90 * 100, 4)
        assert analysis["budget_fit"]["fits_low"] is True
        assert analysis["budget_fit"]["fits_recommended"] is True
        assert analysis["budget_fit"]["fits_high"] is True
        assert "高附加值服务" in analysis["budget_fit"]["recommended_strategy"]
        assert "budget_fit" not in no_budget

        assert "标准报价" in engine._get_pricing_strategy(Decimal("100"), rec)
        assert "低价档" in engine._get_pricing_strategy(Decimal("95"), rec)
        assert "放弃该项目" in engine._get_pricing_strategy(Decimal("60"), rec)

    def test_get_pricing_strategy_and_competitiveness(self):
        engine = PricingEngine()
        rec = engine.generate_recommendations(Decimal("70"), Decimal("0.30"))

        assert engine.get_pricing_strategy(None, Decimal("70")) == "无预算信息,建议按标准报价"
        assert engine.get_pricing_strategy(Decimal("120"), Decimal("70")) == "high"
        assert engine.get_pricing_strategy(Decimal("100"), Decimal("70")) == "medium"
        assert engine.get_pricing_strategy(Decimal("80"), Decimal("70")) == "low"

        assert engine.calculate_competitiveness(rec, None) == Decimal("0.70")
        assert engine.calculate_competitiveness(rec, Decimal("100")) == Decimal("0.90")
        assert engine.calculate_competitiveness(rec, Decimal("95")) == Decimal("0.75")
        assert engine.calculate_competitiveness(rec, Decimal("60")) == Decimal("0.50")
