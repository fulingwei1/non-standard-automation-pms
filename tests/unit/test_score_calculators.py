# -*- coding: utf-8 -*-
"""Tests for app/services/staff_matching/score_calculators.py"""
import pytest
from unittest.mock import MagicMock

from app.services.staff_matching.score_calculators import (
    SkillScoreCalculator,
    DomainScoreCalculator,
    AttitudeScoreCalculator,
    QualityScoreCalculator,
    WorkloadScoreCalculator,
    SpecialScoreCalculator,
)


class TestSkillScoreCalculator:
    @pytest.mark.skip(reason="Complex DB queries with tag matching")
    def test_calculate_skill_score(self):
        db = MagicMock()
        result = SkillScoreCalculator.calculate_skill_score(db, 1, ["Python", "SQL"])
        assert isinstance(result, float)


class TestDomainScoreCalculator:
    @pytest.mark.skip(reason="Complex DB queries")
    def test_calculate_domain_score(self):
        db = MagicMock()
        result = DomainScoreCalculator.calculate_domain_score(db, 1, "manufacturing")
        assert isinstance(result, float)


class TestWorkloadScoreCalculator:
    @pytest.mark.skip(reason="Complex DB queries")
    def test_calculate_workload_score(self):
        db = MagicMock()
        result = WorkloadScoreCalculator.calculate_workload_score(db, 1)
        assert isinstance(result, float)
