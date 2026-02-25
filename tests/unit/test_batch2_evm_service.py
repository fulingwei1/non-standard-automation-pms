# -*- coding: utf-8 -*-
"""EVM Service 测试 - Batch 2"""
from decimal import Decimal
from unittest.mock import MagicMock
import pytest

from app.services.evm_service import EVMCalculator


class TestDecimalConversion:
    def test_from_int(self):
        assert EVMCalculator.decimal(100) == Decimal("100")

    def test_from_float(self):
        assert EVMCalculator.decimal(1.5) == Decimal("1.5")

    def test_from_decimal(self):
        assert EVMCalculator.decimal(Decimal("99.99")) == Decimal("99.99")


class TestRoundDecimal:
    def test_round_4_places(self):
        result = EVMCalculator.round_decimal(Decimal("1.23456789"), 4)
        assert result == Decimal("1.2346")

    def test_round_none(self):
        result = EVMCalculator.round_decimal(None, 4)
        assert result == Decimal("0.0000")

    def test_round_2_places(self):
        result = EVMCalculator.round_decimal(Decimal("3.145"), 2)
        assert result == Decimal("3.15")


class TestScheduleVariance:
    def test_ahead_of_schedule(self):
        sv = EVMCalculator.calculate_schedule_variance(Decimal("500"), Decimal("400"))
        assert sv > 0

    def test_on_schedule(self):
        sv = EVMCalculator.calculate_schedule_variance(Decimal("400"), Decimal("400"))
        assert sv == 0

    def test_behind_schedule(self):
        sv = EVMCalculator.calculate_schedule_variance(Decimal("300"), Decimal("400"))
        assert sv < 0


class TestCostVariance:
    def test_under_budget(self):
        cv = EVMCalculator.calculate_cost_variance(Decimal("500"), Decimal("400"))
        assert cv > 0

    def test_on_budget(self):
        cv = EVMCalculator.calculate_cost_variance(Decimal("400"), Decimal("400"))
        assert cv == 0

    def test_over_budget(self):
        cv = EVMCalculator.calculate_cost_variance(Decimal("300"), Decimal("400"))
        assert cv < 0


class TestSPI:
    def test_ahead(self):
        spi = EVMCalculator.calculate_schedule_performance_index(Decimal("500"), Decimal("400"))
        assert spi > Decimal("1")

    def test_on_schedule(self):
        spi = EVMCalculator.calculate_schedule_performance_index(Decimal("400"), Decimal("400"))
        assert spi == Decimal("1")

    def test_behind(self):
        spi = EVMCalculator.calculate_schedule_performance_index(Decimal("300"), Decimal("400"))
        assert spi < Decimal("1")

    def test_pv_zero(self):
        spi = EVMCalculator.calculate_schedule_performance_index(Decimal("100"), Decimal("0"))
        assert spi is None


class TestCPI:
    def test_efficient(self):
        cpi = EVMCalculator.calculate_cost_performance_index(Decimal("500"), Decimal("400"))
        assert cpi > Decimal("1")

    def test_on_budget(self):
        cpi = EVMCalculator.calculate_cost_performance_index(Decimal("400"), Decimal("400"))
        assert cpi == Decimal("1")

    def test_inefficient(self):
        cpi = EVMCalculator.calculate_cost_performance_index(Decimal("300"), Decimal("400"))
        assert cpi < Decimal("1")

    def test_ac_zero(self):
        cpi = EVMCalculator.calculate_cost_performance_index(Decimal("100"), Decimal("0"))
        assert cpi is None


class TestEAC:
    def test_standard_formula(self):
        eac = EVMCalculator.calculate_estimate_at_completion(
            Decimal("1000"), Decimal("500"), Decimal("600")
        )
        assert eac > 0

    def test_cpi_zero_fallback(self):
        eac = EVMCalculator.calculate_estimate_at_completion(
            Decimal("1000"), Decimal("500"), Decimal("600"), cpi=Decimal("0")
        )
        assert eac == Decimal("1100.0000")

    def test_cpi_none_fallback(self):
        eac = EVMCalculator.calculate_estimate_at_completion(
            Decimal("1000"), Decimal("0"), Decimal("0"), cpi=None
        )
        assert eac == Decimal("1000.0000")

    def test_with_provided_cpi(self):
        eac = EVMCalculator.calculate_estimate_at_completion(
            Decimal("1000"), Decimal("500"), Decimal("600"), cpi=Decimal("0.8")
        )
        expected = Decimal("600") + (Decimal("1000") - Decimal("500")) / Decimal("0.8")
        assert eac == EVMCalculator.round_decimal(expected, 4)


class TestETC:
    def test_positive(self):
        etc = EVMCalculator.calculate_estimate_to_complete(Decimal("1200"), Decimal("600"))
        assert etc == Decimal("600.0000")

    def test_zero(self):
        etc = EVMCalculator.calculate_estimate_to_complete(Decimal("600"), Decimal("600"))
        assert etc == Decimal("0.0000")


class TestVAC:
    def test_savings(self):
        vac = EVMCalculator.calculate_variance_at_completion(Decimal("1000"), Decimal("900"))
        assert vac > 0

    def test_overrun(self):
        vac = EVMCalculator.calculate_variance_at_completion(Decimal("1000"), Decimal("1200"))
        assert vac < 0


class TestTCPI:
    def test_based_on_bac(self):
        tcpi = EVMCalculator.calculate_to_complete_performance_index(
            Decimal("1000"), Decimal("400"), Decimal("500")
        )
        assert tcpi is not None
        assert tcpi > 0

    def test_based_on_eac(self):
        tcpi = EVMCalculator.calculate_to_complete_performance_index(
            Decimal("1000"), Decimal("400"), Decimal("500"), eac=Decimal("1100")
        )
        assert tcpi is not None

    def test_zero_funds_remaining(self):
        tcpi = EVMCalculator.calculate_to_complete_performance_index(
            Decimal("1000"), Decimal("400"), Decimal("1000")
        )
        assert tcpi is None

    def test_eac_equals_ac(self):
        tcpi = EVMCalculator.calculate_to_complete_performance_index(
            Decimal("1000"), Decimal("500"), Decimal("600"), eac=Decimal("600")
        )
        assert tcpi is None


class TestPercentComplete:
    def test_fifty_percent(self):
        result = EVMCalculator.calculate_percent_complete(Decimal("500"), Decimal("1000"))
        assert result == Decimal("50.00")

    def test_zero_bac(self):
        result = EVMCalculator.calculate_percent_complete(Decimal("500"), Decimal("0"))
        assert result is None

    def test_hundred_percent(self):
        result = EVMCalculator.calculate_percent_complete(Decimal("1000"), Decimal("1000"))
        assert result == Decimal("100.00")
