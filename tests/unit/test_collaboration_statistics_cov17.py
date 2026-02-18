# -*- coding: utf-8 -*-
"""第十七批 - 协作评价统计分析单元测试"""
import pytest
from unittest.mock import MagicMock
from decimal import Decimal

pytest.importorskip("app.services.collaboration_rating.statistics")


def _make_stats(db=None):
    from app.services.collaboration_rating.statistics import RatingStatistics
    return RatingStatistics(db or MagicMock(), MagicMock())


class TestRatingStatistics:

    def test_get_average_score_no_ratings_returns_default(self):
        """无评价记录时返回默认值 75.0"""
        db = MagicMock()
        # 单次 filter 调用，返回空列表
        db.query.return_value.filter.return_value.all.return_value = []
        stats = _make_stats(db)
        result = stats.get_average_collaboration_score(engineer_id=1, period_id=1)
        assert result == Decimal("75.0")

    def test_get_average_score_with_ratings(self):
        """有评价记录时计算平均值"""
        db = MagicMock()
        r1 = MagicMock()
        r1.total_score = Decimal("80")
        r2 = MagicMock()
        r2.total_score = Decimal("90")
        db.query.return_value.filter.return_value.all.return_value = [r1, r2]
        stats = _make_stats(db)
        result = stats.get_average_collaboration_score(engineer_id=1, period_id=1)
        assert result == Decimal("85.0")

    def test_get_rating_statistics_no_ratings(self):
        """无评价记录时统计结果为零"""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        stats = _make_stats(db)
        result = stats.get_rating_statistics(period_id=1)
        assert result["total_ratings"] == 0
        assert result["completion_rate"] == 0.0
        assert result["average_score"] == 0.0

    def test_get_rating_statistics_partial_completion(self):
        """部分完成的评价统计"""
        db = MagicMock()

        class FakeRating:
            def __init__(self, score, job_type):
                self.total_score = score
                self.ratee_job_type = job_type

        r1 = FakeRating(Decimal("80"), "mechanical")
        r2 = FakeRating(None, "test")  # 未完成
        db.query.return_value.filter.return_value.all.return_value = [r1, r2]
        stats = _make_stats(db)
        result = stats.get_rating_statistics(period_id=1)
        assert result["total_ratings"] == 2
        assert result["completed_ratings"] == 1
        assert result["pending_ratings"] == 1
        assert result["completion_rate"] == 50.0

    def test_get_rating_statistics_avg_score(self):
        """已完成评价的平均分计算"""
        db = MagicMock()

        class FakeRating:
            def __init__(self, score, job_type):
                self.total_score = score
                self.ratee_job_type = job_type

        r1 = FakeRating(Decimal("70"), "test")
        r2 = FakeRating(Decimal("90"), "test")
        db.query.return_value.filter.return_value.all.return_value = [r1, r2]
        stats = _make_stats(db)
        result = stats.get_rating_statistics(period_id=1)
        assert result["average_score"] == 80.0

    def test_get_average_score_single_rating(self):
        """单个评价时直接返回其分数"""
        db = MagicMock()
        r = MagicMock()
        r.total_score = Decimal("88.5")
        db.query.return_value.filter.return_value.all.return_value = [r]
        stats = _make_stats(db)
        result = stats.get_average_collaboration_score(engineer_id=5, period_id=2)
        assert result == Decimal("88.5")
