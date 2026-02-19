# -*- coding: utf-8 -*-
"""第四十二批：collaboration_rating/statistics.py 单元测试"""
import pytest

pytest.importorskip("app.services.collaboration_rating.statistics")

from decimal import Decimal
from unittest.mock import MagicMock, call
from app.services.collaboration_rating.statistics import RatingStatistics


def make_stats():
    db = MagicMock()
    service = MagicMock()
    return RatingStatistics(db, service), db


def make_rating(total_score, ratee_job_type="mechanical", **extra):
    r = MagicMock()
    r.total_score = total_score
    r.ratee_job_type = ratee_job_type
    for k, v in extra.items():
        setattr(r, k, v)
    return r


# ------------------------------------------------------------------ tests ---

def test_get_average_score_no_ratings_returns_default():
    stats, db = make_stats()
    db.query.return_value.filter.return_value.all.return_value = []
    result = stats.get_average_collaboration_score(1, 1)
    assert result == Decimal("75.0")


def test_get_average_score_with_ratings():
    stats, db = make_stats()
    r1 = make_rating(80)
    r2 = make_rating(90)
    db.query.return_value.filter.return_value.all.return_value = [r1, r2]
    result = stats.get_average_collaboration_score(1, 1)
    assert result == Decimal("85.0")


def test_get_rating_statistics_empty():
    stats, db = make_stats()
    db.query.return_value.filter.return_value.all.return_value = []
    result = stats.get_rating_statistics(1)
    assert result["total_ratings"] == 0
    assert result["completion_rate"] == 0.0


def test_get_rating_statistics_completion():
    stats, db = make_stats()
    r_done = make_rating(80)
    r_pending = MagicMock()
    r_pending.total_score = None
    r_pending.ratee_job_type = "electrical"
    db.query.return_value.filter.return_value.all.return_value = [r_done, r_pending]
    result = stats.get_rating_statistics(1)
    assert result["total_ratings"] == 2
    assert result["completed_ratings"] == 1
    assert result["completion_rate"] == 50.0


def test_analyze_rating_quality_empty():
    stats, db = make_stats()
    db.query.return_value.filter.return_value.all.return_value = []
    result = stats.analyze_rating_quality(1)
    assert result["total_ratings"] == 0
    assert result["quality_analysis"] == {}


def test_analyze_rating_quality_recommendations():
    stats, db = make_stats()
    # avg < 70 → recommendation
    ratings = [make_rating(60, communication_score=60, response_score=60,
                           delivery_score=60, interface_score=60) for _ in range(5)]
    db.query.return_value.filter.return_value.all.return_value = ratings
    result = stats.analyze_rating_quality(1)
    assert any("平均" in r for r in result["recommendations"])


def test_get_collaboration_trend_empty_periods():
    stats, db = make_stats()
    db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
    result = stats.get_collaboration_trend(1, 6)
    assert result["periods_count"] == 0
    assert result["engineer_id"] == 1
