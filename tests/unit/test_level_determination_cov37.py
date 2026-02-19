# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - 等级确定模块
tests/unit/test_level_determination_cov37.py
"""
import pytest
from unittest.mock import MagicMock

pytest.importorskip("app.services.lead_priority_scoring.level_determination")

from app.services.lead_priority_scoring.level_determination import LevelDeterminationMixin


class ConcreteLevelDetermination(LevelDeterminationMixin):
    """具体化混入以便测试"""


class TestDeterminePriorityLevel:
    def setup_method(self):
        self.obj = ConcreteLevelDetermination()

    def test_p1_high_score_and_high_urgency(self):
        assert self.obj._determine_priority_level(80, 8) == "P1"

    def test_p1_very_high_score_and_urgency(self):
        assert self.obj._determine_priority_level(95, 9) == "P1"

    def test_p2_high_score_low_urgency(self):
        assert self.obj._determine_priority_level(75, 5) == "P2"

    def test_p3_low_score_high_urgency(self):
        assert self.obj._determine_priority_level(50, 9) == "P3"

    def test_p4_low_score_low_urgency(self):
        assert self.obj._determine_priority_level(40, 3) == "P4"

    def test_boundary_score_79(self):
        # score < 80 and urgency < 8 → P4
        assert self.obj._determine_priority_level(79, 7) == "P4"


class TestDetermineImportanceLevel:
    def setup_method(self):
        self.obj = ConcreteLevelDetermination()

    def test_high_importance(self):
        assert self.obj._determine_importance_level(80) == "HIGH"

    def test_high_importance_above_80(self):
        assert self.obj._determine_importance_level(100) == "HIGH"

    def test_medium_importance(self):
        assert self.obj._determine_importance_level(60) == "MEDIUM"

    def test_medium_boundary(self):
        assert self.obj._determine_importance_level(79) == "MEDIUM"

    def test_low_importance(self):
        assert self.obj._determine_importance_level(59) == "LOW"


class TestDetermineUrgencyLevel:
    def setup_method(self):
        self.obj = ConcreteLevelDetermination()

    def test_high_urgency(self):
        assert self.obj._determine_urgency_level(8) == "HIGH"

    def test_medium_urgency(self):
        assert self.obj._determine_urgency_level(5) == "MEDIUM"

    def test_low_urgency(self):
        assert self.obj._determine_urgency_level(4) == "LOW"

    def test_low_urgency_zero(self):
        assert self.obj._determine_urgency_level(0) == "LOW"
