# -*- coding: utf-8 -*-
"""
EVM (Earned Value Management) 服务单元测试
覆盖 EVMCalculator 核心计算方法
"""
import pytest
from decimal import Decimal

from app.services.evm_service import EVMCalculator


class TestEVMCalculatorBasics:
    """EVMCalculator 基础工具方法"""

    def test_decimal_converts_float(self):
        result = EVMCalculator.decimal(1.5)
        assert result == Decimal("1.5")

    def test_decimal_converts_int(self):
        result = EVMCalculator.decimal(100)
        assert result == Decimal("100")

    def test_round_decimal_default_4_places(self):
        result = EVMCalculator.round_decimal(Decimal("3.14159265"))
        assert result == Decimal("3.1416")

    def test_round_decimal_custom_places(self):
        result = EVMCalculator.round_decimal(Decimal("3.14159265"), places=2)
        assert result == Decimal("3.14")

    def test_round_decimal_none_returns_zero(self):
        result = EVMCalculator.round_decimal(None)
        assert result == Decimal("0.0000")


class TestScheduleVariance:
    """进度偏差 SV = EV - PV"""

    def test_sv_on_schedule(self):
        sv = EVMCalculator.calculate_schedule_variance(
            ev=Decimal("500"), pv=Decimal("500")
        )
        assert sv == Decimal("0.0000")

    def test_sv_ahead_of_schedule(self):
        sv = EVMCalculator.calculate_schedule_variance(
            ev=Decimal("600"), pv=Decimal("500")
        )
        assert sv == Decimal("100.0000")

    def test_sv_behind_schedule(self):
        sv = EVMCalculator.calculate_schedule_variance(
            ev=Decimal("400"), pv=Decimal("500")
        )
        assert sv == Decimal("-100.0000")


class TestCostVariance:
    """成本偏差 CV = EV - AC"""

    def test_cv_under_budget(self):
        cv = EVMCalculator.calculate_cost_variance(
            ev=Decimal("500"), ac=Decimal("400")
        )
        assert cv == Decimal("100.0000")

    def test_cv_over_budget(self):
        cv = EVMCalculator.calculate_cost_variance(
            ev=Decimal("500"), ac=Decimal("600")
        )
        assert cv == Decimal("-100.0000")

    def test_cv_on_budget(self):
        cv = EVMCalculator.calculate_cost_variance(
            ev=Decimal("500"), ac=Decimal("500")
        )
        assert cv == Decimal("0.0000")


class TestPerformanceIndices:
    """绩效指数 SPI/CPI"""

    def test_spi_on_schedule(self):
        spi = EVMCalculator.calculate_schedule_performance_index(
            ev=Decimal("500"), pv=Decimal("500")
        )
        assert spi == Decimal("1.000000")

    def test_spi_pv_zero_returns_none(self):
        spi = EVMCalculator.calculate_schedule_performance_index(
            ev=Decimal("500"), pv=Decimal("0")
        )
        assert spi is None

    def test_cpi_on_budget(self):
        cpi = EVMCalculator.calculate_cost_performance_index(
            ev=Decimal("500"), ac=Decimal("500")
        )
        assert cpi == Decimal("1.000000")

    def test_cpi_ac_zero_returns_none(self):
        cpi = EVMCalculator.calculate_cost_performance_index(
            ev=Decimal("500"), ac=Decimal("0")
        )
        assert cpi is None

    def test_cpi_under_budget(self):
        cpi = EVMCalculator.calculate_cost_performance_index(
            ev=Decimal("600"), ac=Decimal("500")
        )
        assert cpi > Decimal("1.0")


class TestEACAndETC:
    """完工估算 EAC / 完工尚需 ETC"""

    def test_eac_with_cpi(self):
        cpi = Decimal("0.8")
        # EAC = AC + (BAC - EV) / CPI
        eac = EVMCalculator.calculate_estimate_at_completion(
            bac=Decimal("1000"), ev=Decimal("400"), ac=Decimal("500"), cpi=cpi
        )
        expected = Decimal("500") + (Decimal("1000") - Decimal("400")) / Decimal("0.8")
        assert eac == EVMCalculator.round_decimal(expected, 4)

    def test_eac_without_cpi_uses_simple_formula(self):
        # 当 AC=0 时 CPI=None，退化为 EAC = AC + (BAC - EV)
        eac = EVMCalculator.calculate_estimate_at_completion(
            bac=Decimal("1000"), ev=Decimal("400"), ac=Decimal("0"), cpi=None
        )
        assert eac == Decimal("600.0000")

    def test_etc_equals_eac_minus_ac(self):
        eac = Decimal("1200")
        ac = Decimal("500")
        etc = EVMCalculator.calculate_estimate_to_complete(eac=eac, ac=ac)
        assert etc == Decimal("700.0000")

    def test_vac_positive_means_under_budget(self):
        vac = EVMCalculator.calculate_variance_at_completion(
            bac=Decimal("1000"), eac=Decimal("900")
        )
        assert vac == Decimal("100.0000")


class TestTCPIAndPercentComplete:
    """TCPI / 完成百分比"""

    def test_tcpi_based_on_bac(self):
        tcpi = EVMCalculator.calculate_to_complete_performance_index(
            bac=Decimal("1000"), ev=Decimal("500"), ac=Decimal("600")
        )
        # (1000-500)/(1000-600) = 500/400 = 1.25
        assert tcpi == EVMCalculator.round_decimal(Decimal("1.25"), 6)

    def test_tcpi_zero_denominator_returns_none(self):
        # BAC == AC 时分母为0
        tcpi = EVMCalculator.calculate_to_complete_performance_index(
            bac=Decimal("1000"), ev=Decimal("500"), ac=Decimal("1000")
        )
        assert tcpi is None

    def test_percent_complete(self):
        pct = EVMCalculator.calculate_percent_complete(
            value=Decimal("500"), bac=Decimal("1000")
        )
        assert pct == Decimal("50.00")

    def test_percent_complete_zero_bac_returns_none(self):
        pct = EVMCalculator.calculate_percent_complete(
            value=Decimal("500"), bac=Decimal("0")
        )
        assert pct is None


class TestCalculateAllMetrics:
    """一次性计算所有EVM指标"""

    def test_all_metrics_returns_required_keys(self):
        result = EVMCalculator.calculate_all_metrics(
            pv=500, ev=450, ac=480, bac=1000
        )
        required_keys = ["pv", "ev", "ac", "bac", "sv", "cv", "spi", "cpi",
                         "eac", "etc", "vac", "tcpi"]
        for key in required_keys:
            assert key in result

    def test_all_metrics_sv_calculation(self):
        result = EVMCalculator.calculate_all_metrics(
            pv=500, ev=450, ac=480, bac=1000
        )
        # SV = EV - PV = 450 - 500 = -50
        assert result["sv"] == Decimal("-50.0000")

    def test_all_metrics_cv_calculation(self):
        result = EVMCalculator.calculate_all_metrics(
            pv=500, ev=450, ac=480, bac=1000
        )
        # CV = EV - AC = 450 - 480 = -30
        assert result["cv"] == Decimal("-30.0000")

    def test_all_metrics_on_track_project(self):
        """完美项目：EV==PV==AC"""
        result = EVMCalculator.calculate_all_metrics(
            pv=500, ev=500, ac=500, bac=1000
        )
        assert result["sv"] == Decimal("0.0000")
        assert result["cv"] == Decimal("0.0000")
        assert result["spi"] == Decimal("1.000000")
        assert result["cpi"] == Decimal("1.000000")
