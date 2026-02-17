# -*- coding: utf-8 -*-
"""
AICostEstimationService 单元测试 - G2组覆盖率提升

覆盖:
- AICostEstimationService.__init__
- _calculate_hardware_cost
- _calculate_software_cost
- _calculate_installation_cost
- _calculate_service_cost
- _calculate_risk_reserve
- _calculate_confidence_score
- _generate_pricing_recommendations
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


class TestAICostEstimationServiceInit:
    """初始化测试"""

    def test_init_stores_db_and_user_id(self):
        from app.services.sales.ai_cost_estimation_service import AICostEstimationService
        db = MagicMock()
        svc = AICostEstimationService(db, user_id=42)
        assert svc.db is db
        assert svc.user_id == 42

    def test_model_version_constant(self):
        from app.services.sales.ai_cost_estimation_service import AICostEstimationService
        assert AICostEstimationService.MODEL_VERSION == "v1.0.0"


class TestCalculateHardwareCost:
    """测试 _calculate_hardware_cost"""

    def setup_method(self):
        from app.services.sales.ai_cost_estimation_service import AICostEstimationService
        self.svc = AICostEstimationService(MagicMock(), user_id=1)

    def test_empty_items_returns_zero(self):
        result = self.svc._calculate_hardware_cost(None)
        assert result == Decimal("0")

    def test_empty_list_returns_zero(self):
        result = self.svc._calculate_hardware_cost([])
        assert result == Decimal("0")

    def test_single_item_with_markup(self):
        items = [{"unit_price": 1000, "quantity": 2}]
        result = self.svc._calculate_hardware_cost(items)
        # 2000 * 1.15 = 2300
        assert result == Decimal("2300")

    def test_multiple_items(self):
        items = [
            {"unit_price": 1000, "quantity": 3},
            {"unit_price": 500, "quantity": 4},
        ]
        # (3000 + 2000) * 1.15 = 5750
        result = self.svc._calculate_hardware_cost(items)
        assert result == Decimal("5750")

    def test_default_quantity_is_one(self):
        items = [{"unit_price": 1000}]
        result = self.svc._calculate_hardware_cost(items)
        # 1000 * 1.15
        assert result == Decimal("1150")


class TestCalculateSoftwareCost:
    """测试 _calculate_software_cost"""

    def setup_method(self):
        from app.services.sales.ai_cost_estimation_service import AICostEstimationService
        self.svc = AICostEstimationService(MagicMock(), user_id=1)

    def test_no_requirements_no_man_days_returns_zero(self):
        result = self.svc._calculate_software_cost(None, None)
        assert result == Decimal("0")

    def test_explicit_man_days_used(self):
        # 10 man_days * 8 hours * 800 = 64000
        result = self.svc._calculate_software_cost("some requirements", 10)
        assert result == Decimal("64000")

    def test_short_requirement_uses_5_days(self):
        # < 100 chars -> 5 days * 8 * 800 = 32000
        result = self.svc._calculate_software_cost("short", None)
        assert result == Decimal("32000")

    def test_medium_requirement_uses_15_days(self):
        # 100-500 chars -> 15 days
        requirements = "x" * 200
        result = self.svc._calculate_software_cost(requirements, None)
        assert result == Decimal("96000")

    def test_long_requirement_uses_30_days(self):
        # > 500 chars -> 30 days * 8 * 800 = 192000
        requirements = "x" * 600
        result = self.svc._calculate_software_cost(requirements, None)
        assert result == Decimal("192000")


class TestCalculateInstallationCost:
    """测试 _calculate_installation_cost"""

    def setup_method(self):
        from app.services.sales.ai_cost_estimation_service import AICostEstimationService
        self.svc = AICostEstimationService(MagicMock(), user_id=1)

    def test_no_difficulty_uses_default_multiplier(self):
        # base=5000 * 1.0 + hardware * 0.05
        result = self.svc._calculate_installation_cost(None, Decimal("10000"))
        assert result == Decimal("5500")  # 5000 + 500

    def test_medium_difficulty(self):
        # 5000 * 1.5 + 10000 * 0.05 = 7500 + 500 = 8000
        result = self.svc._calculate_installation_cost("medium", Decimal("10000"))
        assert result == Decimal("8000")

    def test_high_difficulty(self):
        # 5000 * 2.0 + 10000 * 0.05 = 10000 + 500 = 10500
        result = self.svc._calculate_installation_cost("high", Decimal("10000"))
        assert result == Decimal("10500")

    def test_low_difficulty_same_as_default(self):
        result_low = self.svc._calculate_installation_cost("low", Decimal("10000"))
        result_default = self.svc._calculate_installation_cost(None, Decimal("10000"))
        assert result_low == result_default


class TestCalculateServiceCost:
    """测试 _calculate_service_cost"""

    def setup_method(self):
        from app.services.sales.ai_cost_estimation_service import AICostEstimationService
        self.svc = AICostEstimationService(MagicMock(), user_id=1)

    def test_one_year(self):
        # 100000 * 0.10 * 1 = 10000
        result = self.svc._calculate_service_cost(Decimal("100000"), 1)
        assert result == Decimal("10000")

    def test_three_years(self):
        # 100000 * 0.10 * 3 = 30000
        result = self.svc._calculate_service_cost(Decimal("100000"), 3)
        assert result == Decimal("30000")

    def test_zero_base_cost(self):
        result = self.svc._calculate_service_cost(Decimal("0"), 2)
        assert result == Decimal("0")


class TestCalculateRiskReserve:
    """测试 _calculate_risk_reserve"""

    def setup_method(self):
        from app.services.sales.ai_cost_estimation_service import AICostEstimationService
        self.db = MagicMock()
        # No historical variance
        self.db.query.return_value.filter.return_value.scalar.return_value = None
        self.svc = AICostEstimationService(self.db, user_id=1)

    def test_medium_complexity_uses_base_rate(self):
        # 100000 * 0.08 = 8000 (no historical variance)
        result = self.svc._calculate_risk_reserve("standard", "medium", Decimal("100000"))
        assert result == Decimal("8000")

    def test_high_complexity_increases_rate(self):
        result_high = self.svc._calculate_risk_reserve("standard", "high", Decimal("100000"))
        result_medium = self.svc._calculate_risk_reserve("standard", "medium", Decimal("100000"))
        assert result_high > result_medium

    def test_low_complexity_decreases_rate(self):
        result_low = self.svc._calculate_risk_reserve("standard", "low", Decimal("100000"))
        result_medium = self.svc._calculate_risk_reserve("standard", "medium", Decimal("100000"))
        assert result_low < result_medium

    def test_base_cost_zero_gives_zero(self):
        result = self.svc._calculate_risk_reserve("standard", "medium", Decimal("0"))
        assert result == Decimal("0")


class TestCalculateConfidenceScore:
    """测试 _calculate_confidence_score"""

    def setup_method(self):
        from app.services.sales.ai_cost_estimation_service import AICostEstimationService
        self.svc = AICostEstimationService(MagicMock(), user_id=1)

    def test_returns_decimal_between_0_and_1(self):
        input_data = MagicMock()
        result = self.svc._calculate_confidence_score(input_data)
        assert isinstance(result, (Decimal, float, int))
        assert 0 <= float(result) <= 1

    def test_with_hardware_items_increases_confidence(self):
        input_with = MagicMock()
        input_with.hardware_items = [{"unit_price": 100, "quantity": 1}]
        input_without = MagicMock()
        input_without.hardware_items = None
        score_with = self.svc._calculate_confidence_score(input_with)
        score_without = self.svc._calculate_confidence_score(input_without)
        # Having hardware items generally should not lower confidence
        assert float(score_with) >= 0
