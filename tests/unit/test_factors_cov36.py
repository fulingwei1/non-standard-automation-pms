# -*- coding: utf-8 -*-
"""中标率预测因子计算单元测试 - 第三十六批"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock

pytest.importorskip("app.services.win_rate_prediction_service.factors")

try:
    from app.services.win_rate_prediction_service.factors import (
        calculate_base_score,
        calculate_salesperson_factor,
        calculate_customer_factor,
        calculate_competitor_factor,
        calculate_amount_factor,
        calculate_product_factor,
    )
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    calculate_base_score = None


class TestCalculateSalespersonFactor:
    def test_zero_win_rate(self):
        assert calculate_salesperson_factor(0.0) == pytest.approx(0.5)

    def test_full_win_rate(self):
        assert calculate_salesperson_factor(1.0) == pytest.approx(1.0)

    def test_half_win_rate(self):
        assert calculate_salesperson_factor(0.5) == pytest.approx(0.75)


class TestCalculateCustomerFactor:
    def test_deep_cooperation(self):
        factor = calculate_customer_factor(5, 3)
        assert factor == pytest.approx(1.30)

    def test_stable_customer(self):
        factor = calculate_customer_factor(3, 2)
        assert factor == pytest.approx(1.20)

    def test_old_customer(self):
        factor = calculate_customer_factor(1, 0)
        assert factor == pytest.approx(1.10)

    def test_new_customer(self):
        factor = calculate_customer_factor(0, 0)
        assert factor == pytest.approx(1.0)

    def test_repeat_customer(self):
        factor = calculate_customer_factor(0, 0, is_repeat_customer=True)
        assert factor == pytest.approx(1.05)


class TestCalculateCompetitorFactor:
    def test_no_competitors(self):
        assert calculate_competitor_factor(0) == pytest.approx(1.20)

    def test_one_competitor(self):
        assert calculate_competitor_factor(1) == pytest.approx(1.20)

    def test_two_competitors(self):
        assert calculate_competitor_factor(2) == pytest.approx(1.05)

    def test_many_competitors(self):
        assert calculate_competitor_factor(6) == pytest.approx(0.70)


class TestCalculateAmountFactor:
    def test_none_amount(self):
        assert calculate_amount_factor(None) == pytest.approx(1.0)

    def test_small_amount(self):
        assert calculate_amount_factor(Decimal("50000")) == pytest.approx(1.10)

    def test_large_amount(self):
        assert calculate_amount_factor(Decimal("6000000")) == pytest.approx(0.90)


class TestCalculateProductFactor:
    def test_advantage_product(self):
        assert calculate_product_factor("ADVANTAGE") == pytest.approx(1.15)

    def test_new_product(self):
        assert calculate_product_factor("NEW") == pytest.approx(0.85)

    def test_none_type(self):
        assert calculate_product_factor(None) == pytest.approx(1.0)
