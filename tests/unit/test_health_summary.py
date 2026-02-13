# -*- coding: utf-8 -*-
"""健康度汇总单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.strategy.review.health_summary import get_health_score_summary


class TestHealthSummary:
    @patch("app.services.strategy.review.health_summary.get_health_trend")
    @patch("app.services.strategy.review.health_summary.get_dimension_health_details")
    @patch("app.services.strategy.review.health_summary.get_health_level")
    @patch("app.services.strategy.review.health_summary.calculate_strategy_health")
    def test_get_health_score_summary(self, mock_calc, mock_level, mock_details, mock_trend):
        mock_calc.return_value = 85.0
        mock_level.return_value = "HEALTHY"
        mock_details.return_value = [{
            "dimension": "finance",
            "dimension_name": "财务",
            "score": 90,
            "health_level": "HEALTHY",
            "csf_count": 3,
            "kpi_count": 5,
            "kpi_completion_rate": 0.8,
            "kpi_on_track": 4,
            "kpi_at_risk": 1,
            "kpi_off_track": 0,
        }]
        mock_trend.return_value = []
        db = MagicMock()
        result = get_health_score_summary(db, 1)
        assert result.overall_score == 85.0
        assert result.overall_level == "HEALTHY"
        assert len(result.dimensions) == 1

    @patch("app.services.strategy.review.health_summary.get_health_trend")
    @patch("app.services.strategy.review.health_summary.get_dimension_health_details")
    @patch("app.services.strategy.review.health_summary.get_health_level")
    @patch("app.services.strategy.review.health_summary.calculate_strategy_health")
    def test_get_health_score_summary_none(self, mock_calc, mock_level, mock_details, mock_trend):
        mock_calc.return_value = None
        mock_details.return_value = []
        mock_trend.return_value = []
        db = MagicMock()
        result = get_health_score_summary(db, 1)
        assert result.overall_score is None
