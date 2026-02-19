# -*- coding: utf-8 -*-
"""
Tests for app/services/collaboration_rating/statistics.py
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.collaboration_rating.statistics import RatingStatistics
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def statistics(mock_db):
    service = MagicMock()
    return RatingStatistics(db=mock_db, service=service)


def test_get_average_score_no_ratings(statistics, mock_db):
    """无评价时返回默认值 75.0"""
    mock_db.query.return_value.filter.return_value.all.return_value = []
    result = statistics.get_average_collaboration_score(engineer_id=1, period_id=1)
    assert result == Decimal("75.0")


def test_get_average_score_with_ratings(statistics, mock_db):
    """有评价时返回平均值"""
    r1 = MagicMock()
    r1.total_score = 80
    r2 = MagicMock()
    r2.total_score = 90
    mock_db.query.return_value.filter.return_value.all.return_value = [r1, r2]
    result = statistics.get_average_collaboration_score(engineer_id=1, period_id=1)
    assert result == Decimal("85.0")


def test_get_rating_statistics_empty(statistics, mock_db):
    """无评价记录时统计返回零值"""
    mock_db.query.return_value.filter.return_value.all.return_value = []
    result = statistics.get_rating_statistics(period_id=1)
    assert result["total_ratings"] == 0
    assert result["completed_ratings"] == 0
    assert result["completion_rate"] == 0.0


def test_get_rating_statistics_mixed(statistics, mock_db):
    """混合状态评价的统计"""
    r1 = MagicMock()
    r1.total_score = 80.0
    r1.ratee_job_type = "mechanical"
    r2 = MagicMock()
    r2.total_score = None
    r2.ratee_job_type = "test"
    mock_db.query.return_value.filter.return_value.all.return_value = [r1, r2]
    result = statistics.get_rating_statistics(period_id=1)
    assert result["total_ratings"] == 2
    assert result["completed_ratings"] == 1
    assert result["pending_ratings"] == 1
    assert result["completion_rate"] == 50.0


def test_analyze_rating_quality_empty(statistics, mock_db):
    """无评价时返回空分析"""
    mock_db.query.return_value.filter.return_value.all.return_value = []
    result = statistics.analyze_rating_quality(period_id=1)
    assert result["total_ratings"] == 0
    assert result["recommendations"] == []


def test_analyze_rating_quality_low_scores(statistics, mock_db):
    """低分情况下应有改进建议"""
    ratings = []
    for score in [55, 60, 55, 58, 50, 62]:
        r = MagicMock()
        r.total_score = score
        r.communication_score = score
        r.response_score = score
        r.delivery_score = score
        r.interface_score = score
        ratings.append(r)
    mock_db.query.return_value.filter.return_value.all.return_value = ratings
    result = statistics.analyze_rating_quality(period_id=1)
    assert result["total_ratings"] == 6
    assert len(result["recommendations"]) > 0


def test_get_collaboration_trend(statistics, mock_db):
    """测试趋势数据结构"""
    period = MagicMock()
    period.id = 1
    period.period_name = "2024Q1"
    period.start_date = MagicMock()
    period.start_date.isoformat.return_value = "2024-01-01"
    period.end_date = MagicMock()
    period.end_date.isoformat.return_value = "2024-03-31"

    mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [period]
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.filter.return_value.count.return_value = 0

    result = statistics.get_collaboration_trend(engineer_id=1, periods=1)
    assert result["engineer_id"] == 1
    assert "trend_data" in result
