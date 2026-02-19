# -*- coding: utf-8 -*-
"""
Unit tests for WinRatePredictionService (async) (第三十一批)
"""
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.win_rate_prediction_service.service import WinRatePredictionService


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    with patch(
        "app.services.win_rate_prediction_service.service.AIWinRatePredictionService"
    ) as MockAI:
        MockAI.return_value = AsyncMock()
        svc = WinRatePredictionService(db=mock_db)
    return svc


def _make_prediction(pred_id=1, ticket_id=10, score=75.0):
    pred = MagicMock()
    pred.id = pred_id
    pred.presale_ticket_id = ticket_id
    pred.win_rate_score = Decimal(str(score))
    pred.influencing_factors = [
        {"factor": "预算匹配", "score": 0.9},
        {"factor": "技术能力", "score": 0.7},
    ]
    pred.competitor_analysis = {"main_competitor": "竞争对手A", "our_advantage": "价格"}
    return pred


# ---------------------------------------------------------------------------
# predict_win_rate
# ---------------------------------------------------------------------------

class TestPredictWinRate:
    def test_creates_prediction_and_commits(self, service, mock_db):
        ai_result = {
            "win_rate_score": 75.0,
            "confidence_interval": [65.0, 85.0],
            "influencing_factors": [],
            "competitor_analysis": {},
            "improvement_suggestions": [],
            "ai_analysis_report": "预测报告内容",
        }
        service.ai_service.predict_with_ai = AsyncMock(return_value=ai_result)
        service._get_historical_data = AsyncMock(return_value=[])

        with patch(
            "app.services.win_rate_prediction_service.service.PresaleAIWinRate"
        ) as MockPred, patch(
            "app.services.win_rate_prediction_service.service.PresaleWinRateHistory"
        ) as MockHist:
            mock_pred = MagicMock()
            mock_pred.id = 1
            MockPred.return_value = mock_pred
            MockHist.return_value = MagicMock()

            result = asyncio.get_event_loop().run_until_complete(
                service.predict_win_rate(
                    presale_ticket_id=10,
                    ticket_data={"project_name": "测试项目"},
                    created_by=1,
                )
            )

        mock_db.add.assert_called()
        mock_db.commit.assert_awaited_once()
        assert result == mock_pred

    def test_rollback_on_exception(self, service, mock_db):
        service.ai_service.predict_with_ai = AsyncMock(side_effect=Exception("AI error"))
        service._get_historical_data = AsyncMock(return_value=[])

        with pytest.raises(Exception, match="AI error"):
            asyncio.get_event_loop().run_until_complete(
                service.predict_win_rate(
                    presale_ticket_id=10,
                    ticket_data={},
                    created_by=1,
                )
            )

        mock_db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_prediction
# ---------------------------------------------------------------------------

class TestGetPrediction:
    def test_returns_prediction_when_found(self, service, mock_db):
        pred = _make_prediction()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pred
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = asyncio.get_event_loop().run_until_complete(
            service.get_prediction(prediction_id=1)
        )
        assert result == pred

    def test_returns_none_when_not_found(self, service, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = asyncio.get_event_loop().run_until_complete(
            service.get_prediction(prediction_id=999)
        )
        assert result is None


# ---------------------------------------------------------------------------
# get_influencing_factors
# ---------------------------------------------------------------------------

class TestGetInfluencingFactors:
    def test_returns_empty_when_no_prediction(self, service, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = asyncio.get_event_loop().run_until_complete(
            service.get_influencing_factors(ticket_id=99)
        )
        assert result == []

    def test_returns_top_5_factors_sorted(self, service, mock_db):
        pred = _make_prediction()
        pred.influencing_factors = [
            {"factor": f"F{i}", "score": i * 0.1} for i in range(10, 0, -1)
        ]
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pred
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = asyncio.get_event_loop().run_until_complete(
            service.get_influencing_factors(ticket_id=10)
        )
        assert len(result) == 5
        # 应按 score 降序排列
        scores = [f["score"] for f in result]
        assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# get_competitor_analysis
# ---------------------------------------------------------------------------

class TestGetCompetitorAnalysis:
    def test_returns_none_when_no_prediction(self, service, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = asyncio.get_event_loop().run_until_complete(
            service.get_competitor_analysis(ticket_id=99)
        )
        assert result is None

    def test_returns_competitor_data(self, service, mock_db):
        pred = _make_prediction()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pred
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = asyncio.get_event_loop().run_until_complete(
            service.get_competitor_analysis(ticket_id=10)
        )
        assert result is not None
        assert "main_competitor" in result
