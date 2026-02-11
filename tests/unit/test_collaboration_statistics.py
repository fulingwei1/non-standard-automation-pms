# -*- coding: utf-8 -*-
"""Tests for collaboration_rating/statistics.py"""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


class TestRatingStatistics:

    def _make_stats(self):
        from app.services.collaboration_rating.statistics import RatingStatistics
        db = MagicMock()
        service = MagicMock()
        return RatingStatistics(db, service), db

    def test_get_average_score_no_ratings(self):
        stats, db = self._make_stats()
        db.query.return_value.filter.return_value.all.return_value = []
        result = stats.get_average_collaboration_score(1, 1)
        assert result == Decimal("75.0")

    def test_get_average_score_with_ratings(self):
        stats, db = self._make_stats()
        r1 = MagicMock()
        r1.total_score = Decimal("80")
        r2 = MagicMock()
        r2.total_score = Decimal("90")
        db.query.return_value.filter.return_value.all.return_value = [r1, r2]
        result = stats.get_average_collaboration_score(1, 1)
        assert result == Decimal("85.00")

    def test_get_rating_statistics_empty(self):
        stats, db = self._make_stats()
        db.query.return_value.filter.return_value.all.return_value = []
        result = stats.get_rating_statistics(1)
        assert result["total_ratings"] == 0
        assert result["completion_rate"] == 0.0

    def test_get_rating_statistics_with_data(self):
        stats, db = self._make_stats()
        r1 = MagicMock()
        r1.total_score = Decimal("80")
        r1.ratee_job_type = "MECHANICAL"
        r2 = MagicMock()
        r2.total_score = None
        r2.ratee_job_type = None
        db.query.return_value.filter.return_value.all.return_value = [r1, r2]
        result = stats.get_rating_statistics(1)
        assert result["total_ratings"] == 2
        assert result["completed_ratings"] == 1
        assert result["pending_ratings"] == 1
        assert result["completion_rate"] == 50.0

    def test_get_collaboration_trend(self):
        stats, db = self._make_stats()
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"
        period.start_date.isoformat.return_value = "2024-01-01"
        period.end_date.isoformat.return_value = "2024-03-31"
        db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [period]
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.count.return_value = 0

        result = stats.get_collaboration_trend(engineer_id=1, periods=3)
        assert result["engineer_id"] == 1
        assert len(result["trend_data"]) == 1

    def test_analyze_rating_quality_empty(self):
        stats, db = self._make_stats()
        db.query.return_value.filter.return_value.all.return_value = []
        result = stats.analyze_rating_quality(1)
        assert result["total_ratings"] == 0

    def test_analyze_rating_quality_with_data(self):
        stats, db = self._make_stats()
        ratings = []
        for score in [60, 70, 80, 90, 95]:
            r = MagicMock()
            r.total_score = Decimal(str(score))
            r.communication_score = 4
            r.response_score = 3
            r.delivery_score = 4
            r.interface_score = 5
            ratings.append(r)
        db.query.return_value.filter.return_value.all.return_value = ratings
        result = stats.analyze_rating_quality(1)
        assert result["total_ratings"] == 5
        assert "quality_analysis" in result
        assert result["quality_analysis"]["average_score"] == 79.0

    def test_analyze_rating_quality_recommendations(self):
        stats, db = self._make_stats()
        # Low scores with high variance
        ratings = []
        for score in [30, 40, 50, 95, 100]:
            r = MagicMock()
            r.total_score = Decimal(str(score))
            r.communication_score = 2
            r.response_score = 2
            r.delivery_score = 2
            r.interface_score = 2
            ratings.append(r)
        db.query.return_value.filter.return_value.all.return_value = ratings
        result = stats.analyze_rating_quality(1)
        assert len(result["recommendations"]) > 0
