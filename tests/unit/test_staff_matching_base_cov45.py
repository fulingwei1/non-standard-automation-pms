# -*- coding: utf-8 -*-
"""
第四十五批覆盖：staff_matching/base.py
"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.staff_matching.base")

from app.services.staff_matching.base import StaffMatchingBase


class TestStaffMatchingBase:
    def test_dimension_weights_sum_to_one(self):
        total = sum(StaffMatchingBase.DIMENSION_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_dimension_weights_keys(self):
        keys = set(StaffMatchingBase.DIMENSION_WEIGHTS.keys())
        expected = {"skill", "domain", "attitude", "quality", "workload", "special"}
        assert keys == expected

    def test_priority_thresholds_defined(self):
        for priority in ["P1", "P2", "P3", "P4", "P5"]:
            assert priority in StaffMatchingBase.PRIORITY_THRESHOLDS

    def test_p1_has_highest_threshold(self):
        thresholds = StaffMatchingBase.PRIORITY_THRESHOLDS
        assert thresholds["P1"] > thresholds["P5"]

    def test_get_priority_threshold_known(self):
        assert StaffMatchingBase.get_priority_threshold("P1") == 85
        assert StaffMatchingBase.get_priority_threshold("P5") == 50

    def test_get_priority_threshold_unknown_returns_default(self):
        result = StaffMatchingBase.get_priority_threshold("P99")
        assert result == 65  # default

    def test_classify_recommendation_strong(self):
        with patch("app.services.staff_matching.base.RecommendationTypeEnum") as mock_enum:
            mock_enum.STRONG.value = "STRONG"
            mock_enum.RECOMMENDED.value = "RECOMMENDED"
            mock_enum.ACCEPTABLE.value = "ACCEPTABLE"
            mock_enum.WEAK.value = "WEAK"

            result = StaffMatchingBase.classify_recommendation(100, 75)
            assert result == "STRONG"  # 100 >= 75 + 15

    def test_classify_recommendation_recommended(self):
        with patch("app.services.staff_matching.base.RecommendationTypeEnum") as mock_enum:
            mock_enum.STRONG.value = "STRONG"
            mock_enum.RECOMMENDED.value = "RECOMMENDED"
            mock_enum.ACCEPTABLE.value = "ACCEPTABLE"
            mock_enum.WEAK.value = "WEAK"

            result = StaffMatchingBase.classify_recommendation(80, 75)
            assert result == "RECOMMENDED"  # 80 >= 75 but < 90

    def test_classify_recommendation_acceptable(self):
        with patch("app.services.staff_matching.base.RecommendationTypeEnum") as mock_enum:
            mock_enum.STRONG.value = "STRONG"
            mock_enum.RECOMMENDED.value = "RECOMMENDED"
            mock_enum.ACCEPTABLE.value = "ACCEPTABLE"
            mock_enum.WEAK.value = "WEAK"

            result = StaffMatchingBase.classify_recommendation(68, 75)
            assert result == "ACCEPTABLE"  # 68 >= 65 (75-10) but < 75

    def test_classify_recommendation_weak(self):
        with patch("app.services.staff_matching.base.RecommendationTypeEnum") as mock_enum:
            mock_enum.STRONG.value = "STRONG"
            mock_enum.RECOMMENDED.value = "RECOMMENDED"
            mock_enum.ACCEPTABLE.value = "ACCEPTABLE"
            mock_enum.WEAK.value = "WEAK"

            result = StaffMatchingBase.classify_recommendation(50, 75)
            assert result == "WEAK"  # 50 < 65 (75-10)
