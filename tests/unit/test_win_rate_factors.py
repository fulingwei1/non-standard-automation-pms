# -*- coding: utf-8 -*-
from decimal import Decimal
from app.services.win_rate_prediction_service.factors import (
    calculate_salesperson_factor, calculate_customer_factor,
    calculate_competitor_factor, calculate_amount_factor, calculate_product_factor
)


class TestSalespersonFactor:
    def test_zero_rate(self):
        assert calculate_salesperson_factor(0.0) == 0.5

    def test_full_rate(self):
        assert calculate_salesperson_factor(1.0) == 1.0


class TestCustomerFactor:
    def test_deep_cooperation(self):
        assert calculate_customer_factor(5, 3) == 1.30

    def test_stable(self):
        assert calculate_customer_factor(3, 2) == 1.20

    def test_old_customer(self):
        assert calculate_customer_factor(1, 0) == 1.10

    def test_repeat(self):
        assert calculate_customer_factor(0, 0, is_repeat_customer=True) == 1.05

    def test_new(self):
        assert calculate_customer_factor(0, 0) == 1.0


class TestCompetitorFactor:
    def test_no_competition(self):
        assert calculate_competitor_factor(0) == 1.20

    def test_intense(self):
        assert calculate_competitor_factor(5) == 0.85

    def test_extreme(self):
        assert calculate_competitor_factor(10) == 0.70


class TestAmountFactor:
    def test_none(self):
        assert calculate_amount_factor(None) == 1.0

    def test_small(self):
        assert calculate_amount_factor(Decimal("50000")) == 1.10

    def test_large(self):
        assert calculate_amount_factor(Decimal("6000000")) == 0.90


class TestProductFactor:
    def test_advantage(self):
        assert calculate_product_factor("ADVANTAGE") == 1.15

    def test_new(self):
        assert calculate_product_factor("NEW") == 0.85

    def test_none(self):
        assert calculate_product_factor(None) == 1.0
