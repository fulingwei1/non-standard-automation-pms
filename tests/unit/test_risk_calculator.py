# -*- coding: utf-8 -*-
"""
Tests for app/utils/risk_calculator.py
Standalone – no DB, no fixtures.
"""
import pytest
from app.utils.risk_calculator import (
    calculate_risk_level,
    get_risk_score,
    compare_risk_levels,
    RiskCalculator,
)


# ========== calculate_risk_level ==========

class TestCalculateRiskLevel:
    """Full coverage of the risk matrix."""

    # ---- None / empty inputs ----
    def test_none_probability_returns_none(self):
        assert calculate_risk_level(None, "HIGH") is None

    def test_none_impact_returns_none(self):
        assert calculate_risk_level("HIGH", None) is None

    def test_both_none_returns_none(self):
        assert calculate_risk_level(None, None) is None

    def test_empty_probability_returns_none(self):
        assert calculate_risk_level("", "HIGH") is None

    def test_empty_impact_returns_none(self):
        assert calculate_risk_level("HIGH", "") is None

    # ---- CRITICAL ----
    def test_high_high_is_critical(self):
        assert calculate_risk_level("HIGH", "HIGH") == "CRITICAL"

    def test_case_insensitive_critical(self):
        assert calculate_risk_level("high", "high") == "CRITICAL"

    # ---- HIGH ----
    def test_high_medium_is_high(self):
        assert calculate_risk_level("HIGH", "MEDIUM") == "HIGH"

    def test_high_low_is_high(self):
        assert calculate_risk_level("HIGH", "LOW") == "HIGH"

    def test_medium_high_is_high(self):
        assert calculate_risk_level("MEDIUM", "HIGH") == "HIGH"

    def test_low_high_is_high(self):
        assert calculate_risk_level("LOW", "HIGH") == "HIGH"

    # ---- MEDIUM ----
    def test_medium_medium_is_medium(self):
        assert calculate_risk_level("MEDIUM", "MEDIUM") == "MEDIUM"

    def test_medium_low_is_medium(self):
        assert calculate_risk_level("MEDIUM", "LOW") == "MEDIUM"

    def test_low_medium_is_medium(self):
        assert calculate_risk_level("LOW", "MEDIUM") == "MEDIUM"

    # ---- LOW ----
    def test_low_low_is_low(self):
        assert calculate_risk_level("LOW", "LOW") == "LOW"


# ========== get_risk_score ==========

class TestGetRiskScore:
    def test_critical_is_4(self):
        assert get_risk_score("CRITICAL") == 4

    def test_high_is_3(self):
        assert get_risk_score("HIGH") == 3

    def test_medium_is_2(self):
        assert get_risk_score("MEDIUM") == 2

    def test_low_is_1(self):
        assert get_risk_score("LOW") == 1

    def test_case_insensitive(self):
        assert get_risk_score("critical") == 4
        assert get_risk_score("high") == 3

    def test_unknown_returns_0(self):
        assert get_risk_score("UNKNOWN") == 0

    def test_scores_ordered(self):
        assert get_risk_score("LOW") < get_risk_score("MEDIUM") < get_risk_score("HIGH") < get_risk_score("CRITICAL")


# ========== compare_risk_levels ==========

class TestCompareRiskLevels:
    def test_upgrade(self):
        assert compare_risk_levels("MEDIUM", "HIGH") == "UPGRADE"

    def test_upgrade_low_to_critical(self):
        assert compare_risk_levels("LOW", "CRITICAL") == "UPGRADE"

    def test_downgrade(self):
        assert compare_risk_levels("HIGH", "MEDIUM") == "DOWNGRADE"

    def test_downgrade_critical_to_low(self):
        assert compare_risk_levels("CRITICAL", "LOW") == "DOWNGRADE"

    def test_unchanged(self):
        assert compare_risk_levels("HIGH", "HIGH") == "UNCHANGED"

    def test_unchanged_medium(self):
        assert compare_risk_levels("MEDIUM", "MEDIUM") == "UNCHANGED"


# ========== RiskCalculator (class wrapper) ==========

class TestRiskCalculatorClass:
    def test_calculate_risk_level(self):
        assert RiskCalculator.calculate_risk_level("HIGH", "HIGH") == "CRITICAL"

    def test_get_risk_score(self):
        assert RiskCalculator.get_risk_score("HIGH") == 3

    def test_compare_risk_levels(self):
        assert RiskCalculator.compare_risk_levels("LOW", "HIGH") == "UPGRADE"

    def test_instance_methods_work(self):
        calc = RiskCalculator()
        assert calc.calculate_risk_level("LOW", "LOW") == "LOW"
        assert calc.get_risk_score("MEDIUM") == 2
        assert calc.compare_risk_levels("HIGH", "LOW") == "DOWNGRADE"
