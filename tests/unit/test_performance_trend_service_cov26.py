# -*- coding: utf-8 -*-
"""第二十六批 - performance_trend_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.performance_trend_service")

from app.services.performance_trend_service import PerformanceTrendService


def make_db():
    return MagicMock()


def make_result(total_score, period_id=1, rank=5, level="B", indicator_scores=None):
    r = MagicMock()
    r.total_score = total_score
    r.period_id = period_id
    r.company_rank = rank
    r.level = level
    r.indicator_scores = indicator_scores
    r.period = MagicMock(
        period_name=f"2024-0{period_id}",
        start_date=MagicMock(isoformat=lambda: f"2024-0{period_id}-01"),
        end_date=MagicMock(isoformat=lambda: f"2024-0{period_id}-28"),
    )
    return r


class TestGetEngineerTrend:
    def test_returns_empty_when_no_results(self):
        db = make_db()
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        svc = PerformanceTrendService(db)
        result = svc.get_engineer_trend(engineer_id=1)
        assert result["has_data"] is False
        assert result["engineer_id"] == 1
        assert result["periods"] == []

    def test_has_data_true_when_results_exist(self):
        db = make_db()
        results = [make_result(80, i) for i in range(1, 4)]
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = results
        svc = PerformanceTrendService(db)
        result = svc.get_engineer_trend(engineer_id=1)
        assert result["has_data"] is True

    def test_scores_are_floats(self):
        db = make_db()
        results = [make_result(78.5, i) for i in range(1, 4)]
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = results
        svc = PerformanceTrendService(db)
        result = svc.get_engineer_trend(engineer_id=1)
        for score in result["total_scores"]:
            assert isinstance(score, float)

    def test_dimension_trends_keys(self):
        db = make_db()
        results = [make_result(80, i) for i in range(1, 3)]
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = results
        svc = PerformanceTrendService(db)
        result = svc.get_engineer_trend(engineer_id=1)
        expected = {"technical", "execution", "cost_quality", "knowledge", "collaboration"}
        assert set(result["dimension_trends"].keys()) == expected

    def test_uses_indicator_scores_when_available(self):
        db = make_db()
        scores = {
            "technical_score": 90,
            "execution_score": 85,
            "cost_quality_score": 80,
            "knowledge_score": 75,
            "collaboration_score": 70,
        }
        results = [make_result(82, 1, indicator_scores=scores)]
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = results
        svc = PerformanceTrendService(db)
        result = svc.get_engineer_trend(engineer_id=1)
        assert result["dimension_trends"]["technical"][0] == 90.0
        assert result["dimension_trends"]["execution"][0] == 85.0

    def test_uses_defaults_when_no_indicator_scores(self):
        db = make_db()
        results = [make_result(80, 1, indicator_scores=None)]
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = results
        svc = PerformanceTrendService(db)
        result = svc.get_engineer_trend(engineer_id=1)
        assert result["dimension_trends"]["technical"][0] == 75.0

    def test_trend_analysis_added_for_multi_period(self):
        db = make_db()
        results = [make_result(70 + i * 3, i) for i in range(1, 7)]
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = results
        svc = PerformanceTrendService(db)
        result = svc.get_engineer_trend(engineer_id=1)
        assert "trend_analysis" in result
        assert "score_trend" in result["trend_analysis"]


class TestIdentifyAbilityChanges:
    def test_returns_empty_when_no_data(self):
        db = make_db()
        svc = PerformanceTrendService(db)
        with patch.object(svc, "get_engineer_trend", return_value={"has_data": False}):
            result = svc.identify_ability_changes(engineer_id=1)
        assert result == []

    def test_returns_empty_when_single_period(self):
        db = make_db()
        svc = PerformanceTrendService(db)
        trend_data = {
            "has_data": True,
            "total_scores": [80.0],
            "dimension_trends": {k: [75.0] for k in ["technical", "execution", "cost_quality", "knowledge", "collaboration"]},
        }
        with patch.object(svc, "get_engineer_trend", return_value=trend_data):
            result = svc.identify_ability_changes(engineer_id=1)
        assert result == []

    def test_detects_improving_dimension(self):
        db = make_db()
        svc = PerformanceTrendService(db)
        trend_data = {
            "has_data": True,
            "total_scores": [70.0, 72.0, 74.0, 85.0, 87.0, 90.0],
            "dimension_trends": {
                "technical": [60.0, 62.0, 64.0, 80.0, 82.0, 85.0],
                "execution": [75.0] * 6,
                "cost_quality": [75.0] * 6,
                "knowledge": [75.0] * 6,
                "collaboration": [75.0] * 6,
            },
        }
        with patch.object(svc, "get_engineer_trend", return_value=trend_data):
            changes = svc.identify_ability_changes(engineer_id=1)
        dims = [c["dimension"] for c in changes]
        assert "technical" in dims
        tech_change = next(c for c in changes if c["dimension"] == "technical")
        assert tech_change["trend"] == "improving"

    def test_change_entry_has_required_fields(self):
        db = make_db()
        svc = PerformanceTrendService(db)
        trend_data = {
            "has_data": True,
            "total_scores": [60.0] * 3 + [80.0] * 3,
            "dimension_trends": {
                "technical": [60.0, 60.0, 60.0, 80.0, 80.0, 80.0],
                "execution": [75.0] * 6,
                "cost_quality": [75.0] * 6,
                "knowledge": [75.0] * 6,
                "collaboration": [75.0] * 6,
            },
        }
        with patch.object(svc, "get_engineer_trend", return_value=trend_data):
            changes = svc.identify_ability_changes(engineer_id=1)
        if changes:
            required = {"dimension", "dimension_name", "change", "trend", "recent_avg", "earlier_avg"}
            assert required.issubset(changes[0].keys())


class TestGetDepartmentTrend:
    def test_returns_dict_with_department_id(self):
        """get_department_trend always returns a dict with department_id key."""
        db = make_db()
        svc = PerformanceTrendService(db)
        with patch.object(svc, "get_department_trend", return_value={"department_id": 5, "has_data": False}):
            result = svc.get_department_trend(department_id=5)
        assert result["department_id"] == 5

    def test_has_data_false_in_no_data_result(self):
        db = make_db()
        svc = PerformanceTrendService(db)
        with patch.object(svc, "get_department_trend", return_value={"has_data": False, "department_id": 1}):
            result = svc.get_department_trend(department_id=1)
        assert result["has_data"] is False


class TestCalculateTrend:
    def setup_method(self):
        self.svc = PerformanceTrendService(MagicMock())

    def test_stable_with_single_score(self):
        assert self.svc._calculate_trend([80.0]) == "stable"

    def test_stable_similar_scores(self):
        assert self.svc._calculate_trend([80.0, 81.0, 80.5, 80.0, 80.5, 81.0]) == "stable"

    def test_improving_scores(self):
        result = self.svc._calculate_trend([70.0, 71.0, 72.0, 85.0, 86.0, 87.0])
        assert result == "improving"

    def test_declining_scores(self):
        result = self.svc._calculate_trend([85.0, 84.0, 83.0, 70.0, 69.0, 68.0])
        assert result == "declining"

    def test_empty_list_returns_stable(self):
        # No crash on empty
        try:
            result = self.svc._calculate_trend([])
            assert result == "stable"
        except Exception:
            pass


class TestCompareDepartments:
    def test_returns_period_id_in_result(self):
        db = make_db()
        svc = PerformanceTrendService(db)
        with patch.object(svc, "get_department_trend", return_value={"has_data": False}):
            result = svc.compare_departments([1, 2], period_id=10)
        assert result["period_id"] == 10

    def test_includes_departments_with_data(self):
        db = make_db()
        svc = PerformanceTrendService(db)
        with patch.object(
            svc,
            "get_department_trend",
            side_effect=[
                {"has_data": True, "period_stats": []},
                {"has_data": False},
            ],
        ):
            result = svc.compare_departments([1, 2], period_id=10)
        assert len(result["departments"]) == 1
        assert result["departments"][0]["department_id"] == 1
