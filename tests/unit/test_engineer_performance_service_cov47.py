# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - engineer_performance/engineer_performance_service.py
"""
import pytest

pytest.importorskip("app.services.engineer_performance.engineer_performance_service")

from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.engineer_performance.engineer_performance_service import EngineerPerformanceService


def _make_svc():
    db = MagicMock()
    with (
        patch("app.services.engineer_performance.engineer_performance_service.ProfileService"),
        patch("app.services.engineer_performance.engineer_performance_service.DimensionConfigService"),
        patch("app.services.engineer_performance.engineer_performance_service.PerformanceCalculator"),
        patch("app.services.engineer_performance.engineer_performance_service.RankingService"),
    ):
        svc = EngineerPerformanceService(db)
    return svc


def test_init_creates_sub_services():
    svc = _make_svc()
    assert hasattr(svc, "profile_service")
    assert hasattr(svc, "dimension_config_service")
    assert hasattr(svc, "performance_calculator")
    assert hasattr(svc, "ranking_service")


def test_get_engineer_profile_delegates():
    svc = _make_svc()
    svc.profile_service.get_profile.return_value = MagicMock(id=1)
    result = svc.get_engineer_profile(user_id=1)
    svc.profile_service.get_profile.assert_called_once_with(1)
    assert result.id == 1


def test_create_engineer_profile_delegates():
    svc = _make_svc()
    data = MagicMock()
    new_profile = MagicMock()
    svc.profile_service.create_profile.return_value = new_profile
    result = svc.create_engineer_profile(data)
    svc.profile_service.create_profile.assert_called_once_with(data)
    assert result is new_profile


def test_calculate_grade_delegates():
    svc = _make_svc()
    svc.performance_calculator.calculate_grade.return_value = "A"
    grade = svc.calculate_grade(Decimal("90"))
    svc.performance_calculator.calculate_grade.assert_called_once_with(Decimal("90"))
    assert grade == "A"


def test_get_ranking_delegates():
    svc = _make_svc()
    svc.ranking_service.get_ranking.return_value = ([], 0)
    results, total = svc.get_ranking(period_id=1)
    svc.ranking_service.get_ranking.assert_called_once()
    assert total == 0


def test_get_company_summary_delegates():
    svc = _make_svc()
    svc.ranking_service.get_company_summary.return_value = {"avg_score": 80}
    summary = svc.get_company_summary(period_id=2)
    svc.ranking_service.get_company_summary.assert_called_once_with(2)
    assert summary["avg_score"] == 80


def test_list_engineers_delegates():
    svc = _make_svc()
    svc.profile_service.list_profiles.return_value = ([], 0)
    results, total = svc.list_engineers(job_type="ME")
    svc.profile_service.list_profiles.assert_called_once()
    assert total == 0


def test_grade_rules_property():
    svc = _make_svc()
    svc.performance_calculator.GRADE_RULES = {"A": (90, 100)}
    rules = svc.GRADE_RULES
    assert "A" in rules
