# -*- coding: utf-8 -*-
"""
Tests for app/services/staff_matching/base.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.staff_matching.base import StaffMatchingBase
    from app.models.staff_matching import RecommendationTypeEnum
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_dimension_weights_sum_to_one():
    """维度权重之和应等于 1.0"""
    total = sum(StaffMatchingBase.DIMENSION_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9


def test_dimension_weights_keys():
    """维度权重包含所有预期键"""
    expected = {'skill', 'domain', 'attitude', 'quality', 'workload', 'special'}
    assert set(StaffMatchingBase.DIMENSION_WEIGHTS.keys()) == expected


def test_get_priority_threshold_known():
    """已知优先级返回对应阈值"""
    assert StaffMatchingBase.get_priority_threshold("P1") == 85
    assert StaffMatchingBase.get_priority_threshold("P5") == 50


def test_get_priority_threshold_unknown():
    """未知优先级返回默认值 65"""
    result = StaffMatchingBase.get_priority_threshold("UNKNOWN")
    assert result == 65


def test_classify_recommendation_strong():
    """得分远超阈值时分类为 STRONG"""
    with patch("app.services.staff_matching.base.RecommendationTypeEnum") as MockEnum:
        MockEnum.STRONG.value = "STRONG"
        MockEnum.RECOMMENDED.value = "RECOMMENDED"
        MockEnum.ACCEPTABLE.value = "ACCEPTABLE"
        MockEnum.WEAK.value = "WEAK"
        result = StaffMatchingBase.classify_recommendation(95, 70)
        assert result == "STRONG"


def test_classify_recommendation_recommended():
    """得分超过阈值但未到 strong 时分类为 RECOMMENDED"""
    with patch("app.services.staff_matching.base.RecommendationTypeEnum") as MockEnum:
        MockEnum.STRONG.value = "STRONG"
        MockEnum.RECOMMENDED.value = "RECOMMENDED"
        MockEnum.ACCEPTABLE.value = "ACCEPTABLE"
        MockEnum.WEAK.value = "WEAK"
        result = StaffMatchingBase.classify_recommendation(75, 70)
        assert result == "RECOMMENDED"


def test_classify_recommendation_acceptable():
    """得分略低于阈值时分类为 ACCEPTABLE"""
    with patch("app.services.staff_matching.base.RecommendationTypeEnum") as MockEnum:
        MockEnum.STRONG.value = "STRONG"
        MockEnum.RECOMMENDED.value = "RECOMMENDED"
        MockEnum.ACCEPTABLE.value = "ACCEPTABLE"
        MockEnum.WEAK.value = "WEAK"
        result = StaffMatchingBase.classify_recommendation(62, 70)
        assert result == "ACCEPTABLE"


def test_classify_recommendation_weak():
    """得分远低于阈值时分类为 WEAK"""
    with patch("app.services.staff_matching.base.RecommendationTypeEnum") as MockEnum:
        MockEnum.STRONG.value = "STRONG"
        MockEnum.RECOMMENDED.value = "RECOMMENDED"
        MockEnum.ACCEPTABLE.value = "ACCEPTABLE"
        MockEnum.WEAK.value = "WEAK"
        result = StaffMatchingBase.classify_recommendation(40, 70)
        assert result == "WEAK"


def test_priority_thresholds_all_defined():
    """所有优先级阈值应已定义"""
    for p in ["P1", "P2", "P3", "P4", "P5"]:
        assert p in StaffMatchingBase.PRIORITY_THRESHOLDS
