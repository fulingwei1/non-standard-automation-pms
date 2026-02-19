# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - quality_risk_ai/test_recommendation_engine.py
"""
import pytest

pytest.importorskip("app.services.quality_risk_ai.test_recommendation_engine")

from app.services.quality_risk_ai.test_recommendation_engine import TestRecommendationEngine


def _engine():
    return TestRecommendationEngine()


BASE_RISK = {
    "risk_level": "HIGH",
    "risk_score": 70,
    "risk_category": "BUG",
    "risk_signals": [],
    "predicted_issues": [],
    "abnormal_patterns": [],
    "risk_keywords": {},
}


def test_generate_recommendations_structure():
    engine = _engine()
    result = engine.generate_recommendations(BASE_RISK, {})
    assert "focus_areas" in result
    assert "test_types" in result
    assert "priority_level" in result
    assert "recommended_testers" in result
    assert "recommended_days" in result


def test_determine_priority_urgent():
    engine = _engine()
    assert engine._determine_priority("CRITICAL", 90) == "URGENT"


def test_determine_priority_low():
    engine = _engine()
    assert engine._determine_priority("LOW", 10) == "LOW"


def test_recommend_test_types_bug_category():
    engine = _engine()
    types = engine._recommend_test_types("BUG", {})
    assert "功能测试" in types


def test_recommend_test_types_default():
    engine = _engine()
    types = engine._recommend_test_types(None, {})
    assert len(types) >= 1


def test_calculate_coverage_target_critical():
    engine = _engine()
    assert engine._calculate_coverage_target("CRITICAL") == 95.0


def test_calculate_coverage_target_low():
    engine = _engine()
    assert engine._calculate_coverage_target("LOW") == 65.0


def test_identify_focus_areas_from_signals():
    engine = _engine()
    risk_analysis = {
        **BASE_RISK,
        "risk_signals": [
            {"module": "登录模块", "risk_score": 80}
        ]
    }
    areas = engine._identify_focus_areas(risk_analysis)
    assert any(a["area"] == "登录模块" for a in areas)


def test_calculate_resource_needs_high_risk():
    engine = _engine()
    res = engine._calculate_resource_needs("HIGH", 3, {})
    assert res["testers"] >= 1
    assert res["days"] >= 3


def test_generate_risk_summary_includes_level():
    engine = _engine()
    summary = engine._generate_risk_summary(BASE_RISK)
    assert "HIGH" in summary
