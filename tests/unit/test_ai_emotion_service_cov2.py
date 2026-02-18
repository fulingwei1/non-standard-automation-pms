# -*- coding: utf-8 -*-
"""
ai_emotion_service.py 单元测试（第二批）
使用 Mock 绕过 OpenAI 调用
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, AsyncMock


def _make_service(mock_db=None):
    """创建 AIEmotionService 实例（绕过环境变量）"""
    from app.services.ai_emotion_service import AIEmotionService
    if mock_db is None:
        mock_db = MagicMock()
    return AIEmotionService(mock_db)


# ─── 1. _determine_sentiment ──────────────────────────────────────────────────
def test_determine_sentiment_positive():
    from app.services.ai_emotion_service import SentimentType
    svc = _make_service()
    assert svc._determine_sentiment(50.0) == SentimentType.POSITIVE


def test_determine_sentiment_negative():
    from app.services.ai_emotion_service import SentimentType
    svc = _make_service()
    assert svc._determine_sentiment(-50.0) == SentimentType.NEGATIVE


def test_determine_sentiment_neutral():
    from app.services.ai_emotion_service import SentimentType
    svc = _make_service()
    assert svc._determine_sentiment(0.0) == SentimentType.NEUTRAL
    assert svc._determine_sentiment(29.9) == SentimentType.NEUTRAL
    assert svc._determine_sentiment(-29.9) == SentimentType.NEUTRAL


# ─── 2. _determine_churn_risk ────────────────────────────────────────────────
def test_determine_churn_risk_high():
    from app.services.ai_emotion_service import ChurnRiskLevel
    svc = _make_service()
    result = svc._determine_churn_risk({"risk_score": 80})
    assert result == ChurnRiskLevel.HIGH


def test_determine_churn_risk_medium():
    from app.services.ai_emotion_service import ChurnRiskLevel
    svc = _make_service()
    result = svc._determine_churn_risk({"risk_score": 50})
    assert result == ChurnRiskLevel.MEDIUM


def test_determine_churn_risk_low():
    from app.services.ai_emotion_service import ChurnRiskLevel
    svc = _make_service()
    result = svc._determine_churn_risk({"risk_score": 20})
    assert result == ChurnRiskLevel.LOW


def test_determine_churn_risk_default():
    from app.services.ai_emotion_service import ChurnRiskLevel
    svc = _make_service()
    # 没有 risk_score key，默认50 -> MEDIUM
    result = svc._determine_churn_risk({})
    assert result == ChurnRiskLevel.MEDIUM


# ─── 3. _determine_priority ──────────────────────────────────────────────────
def test_determine_priority_high():
    from app.services.ai_emotion_service import ReminderPriority
    svc = _make_service()
    assert svc._determine_priority("high") == ReminderPriority.HIGH


def test_determine_priority_low():
    from app.services.ai_emotion_service import ReminderPriority
    svc = _make_service()
    assert svc._determine_priority("low") == ReminderPriority.LOW


def test_determine_priority_medium():
    from app.services.ai_emotion_service import ReminderPriority
    svc = _make_service()
    assert svc._determine_priority("medium") == ReminderPriority.MEDIUM


# ─── 4. _calculate_recommended_time ─────────────────────────────────────────
def test_calculate_recommended_time_high():
    svc = _make_service()
    before = datetime.now()
    result = svc._calculate_recommended_time("high")
    after = datetime.now()
    # 应该在2小时左右
    assert (result - before).total_seconds() >= 7190
    assert (result - before).total_seconds() <= 7210


def test_calculate_recommended_time_low():
    svc = _make_service()
    result = svc._calculate_recommended_time("low")
    expected = datetime.now() + timedelta(days=3)
    diff = abs((result - expected).total_seconds())
    assert diff < 5  # 5秒内


def test_calculate_recommended_time_medium():
    svc = _make_service()
    result = svc._calculate_recommended_time("medium")
    expected = datetime.now() + timedelta(days=1)
    diff = abs((result - expected).total_seconds())
    assert diff < 5


# ─── 5. batch_analyze_customers（async）────────────────────────────────────────
import asyncio

def test_batch_analyze_customers_no_analysis():
    svc = _make_service()
    # db.query().filter().order_by().first() returns None
    svc.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    result = asyncio.run(svc.batch_analyze_customers([1, 2]))
    assert result["total_analyzed"] == 2
    assert result["success_count"] == 2
    assert len(result["summaries"]) == 2
    # 没有情绪分析时，sentiment 应为 None
    assert result["summaries"][0]["latest_sentiment"] is None


def test_batch_analyze_customers_with_analysis():
    from app.services.ai_emotion_service import SentimentType, ChurnRiskLevel
    svc = _make_service()

    mock_analysis = MagicMock()
    mock_analysis.sentiment = SentimentType.POSITIVE
    mock_analysis.purchase_intent_score = Decimal("75.0")
    mock_analysis.churn_risk = ChurnRiskLevel.LOW

    svc.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_analysis

    result = asyncio.run(svc.batch_analyze_customers([10]))
    assert result["success_count"] == 1
    assert result["summaries"][0]["latest_sentiment"] == "positive"


# ─── 6. _identify_turning_points ─────────────────────────────────────────────
def test_identify_turning_points_empty():
    svc = _make_service()
    result = svc._identify_turning_points([])
    assert result == []


def test_identify_turning_points_single():
    svc = _make_service()
    data = [{"sentiment": "positive", "intent_score": 80}]
    result = svc._identify_turning_points(data)
    # 单点无转折
    assert isinstance(result, list)
