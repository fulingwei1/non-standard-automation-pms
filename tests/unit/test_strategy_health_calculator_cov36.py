# -*- coding: utf-8 -*-
"""战略管理健康度计算器单元测试 - 第三十六批"""

import pytest
from unittest.mock import MagicMock

pytest.importorskip("app.services.strategy.health_calculator")

try:
    from app.services.strategy.health_calculator import (
        calculate_kpi_completion_rate,
        get_health_level,
    )
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    calculate_kpi_completion_rate = None


def make_kpi(current=None, target=None, direction="UP"):
    kpi = MagicMock()
    kpi.current_value = current
    kpi.target_value = target
    kpi.direction = direction
    return kpi


class TestCalculateKpiCompletionRate:
    def test_no_target_returns_none(self):
        kpi = make_kpi(current=50, target=None)
        assert calculate_kpi_completion_rate(kpi) is None

    def test_zero_target_returns_none(self):
        kpi = make_kpi(current=50, target=0)
        assert calculate_kpi_completion_rate(kpi) is None

    def test_no_current_returns_zero(self):
        kpi = make_kpi(current=None, target=100, direction="UP")
        assert calculate_kpi_completion_rate(kpi) == 0

    def test_up_direction_full_completion(self):
        kpi = make_kpi(current=100, target=100, direction="UP")
        assert calculate_kpi_completion_rate(kpi) == pytest.approx(100.0)

    def test_up_direction_over_completion_capped_at_150(self):
        kpi = make_kpi(current=200, target=100, direction="UP")
        result = calculate_kpi_completion_rate(kpi)
        assert result == pytest.approx(150.0)

    def test_down_direction_current_equals_target(self):
        kpi = make_kpi(current=50, target=50, direction="DOWN")
        result = calculate_kpi_completion_rate(kpi)
        assert result == pytest.approx(100.0)

    def test_down_direction_zero_current(self):
        kpi = make_kpi(current=0, target=50, direction="DOWN")
        result = calculate_kpi_completion_rate(kpi)
        assert result == pytest.approx(150.0)  # capped at 150


class TestGetHealthLevel:
    def test_excellent_score(self):
        assert get_health_level(95) == "EXCELLENT"

    def test_good_score(self):
        assert get_health_level(75) == "GOOD"

    def test_warning_score(self):
        assert get_health_level(55) == "WARNING"

    def test_danger_score(self):
        assert get_health_level(30) == "DANGER"

    def test_boundary_90_is_excellent(self):
        assert get_health_level(90) == "EXCELLENT"

    def test_boundary_70_is_good(self):
        assert get_health_level(70) == "GOOD"

    def test_boundary_50_is_warning(self):
        assert get_health_level(50) == "WARNING"
