# -*- coding: utf-8 -*-
"""等级确定模块单元测试"""
import pytest
from app.services.lead_priority_scoring.level_determination import LevelDeterminationMixin


class TestLevelDeterminationMixin:
    def setup_method(self):
        self.mixin = LevelDeterminationMixin()

    def test_priority_p1(self):
        assert self.mixin._determine_priority_level(85, 9) == "P1"

    def test_priority_p2(self):
        assert self.mixin._determine_priority_level(75, 5) == "P2"

    def test_priority_p3(self):
        assert self.mixin._determine_priority_level(50, 9) == "P3"

    def test_priority_p4(self):
        assert self.mixin._determine_priority_level(50, 5) == "P4"

    def test_importance_high(self):
        assert self.mixin._determine_importance_level(85) == "HIGH"

    def test_importance_medium(self):
        assert self.mixin._determine_importance_level(65) == "MEDIUM"

    def test_importance_low(self):
        assert self.mixin._determine_importance_level(40) == "LOW"

    def test_urgency_high(self):
        assert self.mixin._determine_urgency_level(9) == "HIGH"

    def test_urgency_medium(self):
        assert self.mixin._determine_urgency_level(6) == "MEDIUM"

    def test_urgency_low(self):
        assert self.mixin._determine_urgency_level(3) == "LOW"
