# -*- coding: utf-8 -*-
"""
Tests for app/utils/project_utils.py
Tests for the ProjectUtils class (pure calculation logic, no DB needed).
"""
import pytest
from app.utils.project_utils import ProjectUtils


class TestProjectUtilsHealthScore:
    """ProjectUtils.calculate_health_score"""

    def setup_method(self):
        self.pu = ProjectUtils()

    def test_perfect_score(self):
        metrics = {
            "schedule_performance": 1.0,
            "cost_performance": 1.0,
            "quality_score": 100,
            "team_satisfaction": 5.0,
        }
        score = self.pu.calculate_health_score(metrics)
        assert score == 100.0

    def test_all_zeros(self):
        metrics = {
            "schedule_performance": 0.0,
            "cost_performance": 0.0,
            "quality_score": 0,
            "team_satisfaction": 0.0,
        }
        score = self.pu.calculate_health_score(metrics)
        assert score == 0.0

    def test_spi_capped_at_1(self):
        """SPI > 1 should be capped to 1."""
        metrics = {
            "schedule_performance": 1.5,  # capped to 1.0
            "cost_performance": 1.0,
            "quality_score": 100,
            "team_satisfaction": 5.0,
        }
        score = self.pu.calculate_health_score(metrics)
        assert score == 100.0

    def test_cpi_capped_at_1(self):
        """CPI > 1 should be capped to 1."""
        metrics = {
            "schedule_performance": 1.0,
            "cost_performance": 2.0,  # capped to 1.0
            "quality_score": 100,
            "team_satisfaction": 5.0,
        }
        score = self.pu.calculate_health_score(metrics)
        assert score == 100.0

    def test_empty_metrics_uses_defaults(self):
        """With empty dict, defaults should give a reasonable score."""
        score = self.pu.calculate_health_score({})
        # Defaults: spi=1.0, cpi=1.0, quality=80/100, satisfaction=4/5
        # = 1.0*30 + 1.0*30 + 0.8*20 + 0.8*20 = 30+30+16+16 = 92
        assert 0 <= score <= 100

    def test_score_is_float(self):
        score = self.pu.calculate_health_score({"quality_score": 75})
        assert isinstance(score, float)

    def test_score_clamped_to_0_100(self):
        """Score should always be between 0 and 100."""
        for q in [0, 50, 100]:
            metrics = {"quality_score": q, "schedule_performance": 0.5}
            score = self.pu.calculate_health_score(metrics)
            assert 0 <= score <= 100

    def test_partial_metrics(self):
        """Only some metrics provided."""
        metrics = {"schedule_performance": 0.8, "cost_performance": 0.9}
        score = self.pu.calculate_health_score(metrics)
        assert 0 <= score <= 100


class TestProjectUtilsEstimateDuration:
    """ProjectUtils.estimate_duration"""

    def setup_method(self):
        self.pu = ProjectUtils()

    def test_basic_estimate(self):
        params = {
            "effort_person_days": 20,
            "team_size": 2,
            "complexity_factor": 1.0,
        }
        weeks = self.pu.estimate_duration(params)
        assert weeks == 2.0  # 20 / 2 / 5 * 1.0 = 2.0

    def test_complexity_multiplier(self):
        params = {
            "effort_person_days": 10,
            "team_size": 1,
            "complexity_factor": 2.0,
        }
        weeks = self.pu.estimate_duration(params)
        assert weeks == 4.0  # 10 / 1 / 5 * 2.0 = 4.0

    def test_defaults(self):
        """With empty params, uses defaults: effort=30, team=1, complexity=1.0."""
        weeks = self.pu.estimate_duration({})
        assert weeks == 6.0  # 30 / 1 / 5 * 1.0

    def test_zero_team_size_safe(self):
        """team_size <= 0 should be treated as 1."""
        params = {"effort_person_days": 10, "team_size": 0, "complexity_factor": 1.0}
        weeks = self.pu.estimate_duration(params)
        assert weeks == 2.0  # 10 / 1 / 5 = 2.0 (because max(0, 1) = 1)

    def test_result_is_float(self):
        weeks = self.pu.estimate_duration({"effort_person_days": 10})
        assert isinstance(weeks, float)

    def test_large_team_short_duration(self):
        params = {
            "effort_person_days": 100,
            "team_size": 10,
            "complexity_factor": 1.0,
        }
        weeks = self.pu.estimate_duration(params)
        assert weeks == 2.0  # 100 / 10 / 5 = 2.0
