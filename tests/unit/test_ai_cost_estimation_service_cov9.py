# -*- coding: utf-8 -*-
"""第九批: test_ai_cost_estimation_service_cov9.py - AICostEstimationService 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

pytest.importorskip("app.services.sales.ai_cost_estimation_service")

from app.services.sales.ai_cost_estimation_service import AICostEstimationService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return AICostEstimationService(db=mock_db, user_id=1)


class TestAICostEstimationServiceInit:
    def test_init(self, service, mock_db):
        assert service.db is mock_db
        assert service.user_id == 1
        assert service.MODEL_VERSION == "v1.0.0"

    def test_constants(self, service):
        assert service.HARDWARE_MARKUP == Decimal("1.15")
        assert service.SOFTWARE_HOURLY_RATE == Decimal("800")


class TestCalculateHardwareCost:
    """测试硬件成本计算: _calculate_hardware_cost(hardware_items)"""

    def test_empty_hardware_items(self, service):
        result = service._calculate_hardware_cost(None)
        assert result == Decimal("0")

    def test_hardware_items_with_markup(self, service):
        items = [{"unit_price": "10000", "quantity": "2"}]
        result = service._calculate_hardware_cost(items)
        expected = Decimal("10000") * Decimal("2") * Decimal("1.15")
        assert result == expected

    def test_multiple_items(self, service):
        items = [
            {"unit_price": "5000", "quantity": "3"},
            {"unit_price": "2000", "quantity": "1"}
        ]
        result = service._calculate_hardware_cost(items)
        expected = (Decimal("5000") * 3 + Decimal("2000")) * Decimal("1.15")
        assert result == expected


class TestCalculateSoftwareCost:
    """测试软件成本计算: _calculate_software_cost(requirements, man_days)"""

    def test_software_cost_with_man_days(self, service):
        result = service._calculate_software_cost("描述", man_days=10)
        expected = Decimal("10") * Decimal("8") * Decimal("800")
        assert result == expected

    def test_software_cost_no_requirements_no_days(self, service):
        result = service._calculate_software_cost(None, man_days=None)
        assert result == Decimal("0")

    def test_software_cost_short_requirements(self, service):
        # < 100 words -> 5 man_days
        result = service._calculate_software_cost("短需求", man_days=None)
        expected = Decimal("5") * Decimal("8") * Decimal("800")
        assert result == expected


class TestCalculateInstallationCost:
    """测试安装成本计算: _calculate_installation_cost(difficulty, hardware_cost)"""

    def test_installation_cost_easy(self, service):
        hardware_cost = Decimal("100000")
        result = service._calculate_installation_cost("low", hardware_cost)
        expected = Decimal("5000") * Decimal("1.0") + hardware_cost * Decimal("0.05")
        assert result == expected

    def test_installation_cost_high(self, service):
        hardware_cost = Decimal("100000")
        result = service._calculate_installation_cost("high", hardware_cost)
        expected = Decimal("5000") * Decimal("2.0") + hardware_cost * Decimal("0.05")
        assert result == expected

    def test_installation_high_greater_than_low(self, service):
        hw = Decimal("50000")
        assert service._calculate_installation_cost("high", hw) > service._calculate_installation_cost("low", hw)


class TestCalculateServiceCost:
    """测试服务成本计算"""

    def test_service_cost(self, service):
        base = Decimal("100000")
        result = service._calculate_service_cost(base, years=2)
        expected = base * Decimal("0.10") * Decimal("2")
        assert result == expected


class TestCalculateRiskReserve:
    """测试风险储备金计算"""

    def test_risk_reserve_normal(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        with patch.object(service, "_get_historical_variance", return_value=None):
            result = service._calculate_risk_reserve("automation", "medium", Decimal("100000"))
            assert result > Decimal("0")

    def test_risk_reserve_high_complexity(self, service):
        with patch.object(service, "_get_historical_variance", return_value=None):
            low = service._calculate_risk_reserve("automation", "low", Decimal("100000"))
            high = service._calculate_risk_reserve("automation", "high", Decimal("100000"))
            assert high > low


class TestCalculateConfidenceScore:
    """测试置信度评分"""

    def test_confidence_score(self, service, mock_db):
        input_data = MagicMock()
        input_data.hardware_items = [{"unit_price": "1000", "quantity": "1"}]
        input_data.software_requirements = "x" * 200  # > 100 chars
        input_data.estimated_man_days = 10
        input_data.project_type = "automation"
        # Mock DB query for historical count
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        result = service._calculate_confidence_score(input_data)
        assert isinstance(result, Decimal)
        assert Decimal("0") <= result <= Decimal("1")
