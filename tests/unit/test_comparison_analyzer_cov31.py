# -*- coding: utf-8 -*-
"""
Unit tests for ProjectComparisonAnalyzer (第三十一批)
"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.project_review_ai.comparison_analyzer import ProjectComparisonAnalyzer


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def analyzer(mock_db):
    with patch(
        "app.services.project_review_ai.comparison_analyzer.AIClientService"
    ) as MockAI:
        MockAI.return_value = MagicMock()
        svc = ProjectComparisonAnalyzer(db=mock_db)
    return svc


def _make_review(review_id=1, status="PUBLISHED", budget=500000.0):
    review = MagicMock()
    review.id = review_id
    review.status = status
    review.budget_amount = budget
    review.quality_score = 85.0
    review.project = MagicMock()
    review.project.industry = "制造业"
    review.project.project_type = "非标自动化"
    return review


# ---------------------------------------------------------------------------
# compare_with_history
# ---------------------------------------------------------------------------

class TestCompareWithHistory:
    def test_raises_when_review_not_found(self, analyzer, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = None

        with pytest.raises(ValueError, match="复盘报告"):
            analyzer.compare_with_history(review_id=999)

    def test_returns_dict_with_required_keys(self, analyzer, mock_db):
        review = _make_review()
        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            chain = MagicMock()
            chain.filter.return_value = chain
            chain.join.return_value = chain
            chain.order_by.return_value = chain
            chain.limit.return_value = chain
            chain.all.return_value = []
            chain.first.return_value = review if call_count[0] == 1 else None
            return chain

        mock_db.query.side_effect = query_side_effect

        with patch.object(
            analyzer, "_analyze_comparison", return_value={"improvements": [], "benchmarks": {}}
        ), patch.object(
            analyzer, "_format_review", return_value={}
        ):
            result = analyzer.compare_with_history(review_id=1)

        assert "current_review" in result
        assert "similar_reviews" in result
        assert "improvements" in result

    def test_returns_empty_similar_reviews_when_none_found(self, analyzer, mock_db):
        review = _make_review()
        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            chain = MagicMock()
            chain.filter.return_value = chain
            chain.join.return_value = chain
            chain.order_by.return_value = chain
            chain.limit.return_value = chain
            chain.all.return_value = []
            chain.first.return_value = review if call_count[0] == 1 else None
            return chain

        mock_db.query.side_effect = query_side_effect

        with patch.object(
            analyzer, "_analyze_comparison", return_value={"improvements": [], "benchmarks": {}}
        ), patch.object(
            analyzer, "_format_review", return_value={}
        ):
            result = analyzer.compare_with_history(review_id=1)

        assert result["similar_reviews"] == []


# ---------------------------------------------------------------------------
# _find_similar_reviews
# ---------------------------------------------------------------------------

class TestFindSimilarReviews:
    def test_industry_similarity(self, analyzer, mock_db):
        current = _make_review()
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.join.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = []

        result = analyzer._find_similar_reviews(current, "industry", limit=5)
        assert result == []

    def test_scale_similarity_filters_by_budget_range(self, analyzer, mock_db):
        current = _make_review(budget=100000.0)
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.join.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = []

        result = analyzer._find_similar_reviews(current, "scale", limit=3)
        assert result == []


# ---------------------------------------------------------------------------
# identify_improvements
# ---------------------------------------------------------------------------

class TestIdentifyImprovements:
    def test_returns_empty_list_when_no_improvements(self, analyzer):
        with patch.object(
            analyzer,
            "compare_with_history",
            return_value={"analysis": {"improvements": [], "benchmarks": {}}},
        ):
            result = analyzer.identify_improvements(review_id=1)
        assert result == []

    def test_sorts_by_priority(self, analyzer):
        improvements = [
            {"title": "低优先级", "priority": "LOW", "estimated_impact": 10},
            {"title": "高优先级", "priority": "HIGH", "estimated_impact": 80},
        ]
        with patch.object(
            analyzer,
            "compare_with_history",
            return_value={"analysis": {"improvements": improvements, "benchmarks": {}}},
        ), patch.object(
            analyzer, "_calculate_priority", side_effect=lambda x: x["priority"]
        ), patch.object(
            analyzer, "_assess_feasibility", return_value="HIGH"
        ), patch.object(
            analyzer, "_estimate_impact", side_effect=lambda x: x.get("estimated_impact", 0)
        ):
            result = analyzer.identify_improvements(review_id=1)

        # HIGH 优先级应排第一
        assert result[0]["priority"] == "HIGH"
