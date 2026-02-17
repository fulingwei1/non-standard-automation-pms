# -*- coding: utf-8 -*-
"""
E组 - AI情绪分析服务 单元测试
覆盖: app/services/ai_emotion_service.py
"""
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─── fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def service(db_session):
    from app.services.ai_emotion_service import AIEmotionService
    svc = AIEmotionService(db_session)
    return svc


# ─── _determine_sentiment ───────────────────────────────────────────────────

class TestDetermineSentiment:

    def test_positive_score(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType
        result = service._determine_sentiment(50)
        assert result == SentimentType.POSITIVE

    def test_negative_score(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType
        result = service._determine_sentiment(-50)
        assert result == SentimentType.NEGATIVE

    def test_neutral_score_zero(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType
        result = service._determine_sentiment(0)
        assert result == SentimentType.NEUTRAL

    def test_boundary_positive(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType
        result = service._determine_sentiment(31)
        assert result == SentimentType.POSITIVE

    def test_boundary_negative(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType
        result = service._determine_sentiment(-31)
        assert result == SentimentType.NEGATIVE

    def test_neutral_range(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType
        for score in [0, 10, -10, 29, -29]:
            result = service._determine_sentiment(score)
            assert result == SentimentType.NEUTRAL


# ─── _determine_churn_risk ──────────────────────────────────────────────────

class TestDetermineChurnRisk:

    def test_high_risk(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel
        result = service._determine_churn_risk({"risk_score": 75})
        assert result == ChurnRiskLevel.HIGH

    def test_medium_risk(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel
        result = service._determine_churn_risk({"risk_score": 50})
        assert result == ChurnRiskLevel.MEDIUM

    def test_low_risk(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel
        result = service._determine_churn_risk({"risk_score": 20})
        assert result == ChurnRiskLevel.LOW

    def test_boundary_high(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel
        result = service._determine_churn_risk({"risk_score": 70})
        assert result == ChurnRiskLevel.HIGH

    def test_boundary_medium(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel
        result = service._determine_churn_risk({"risk_score": 40})
        assert result == ChurnRiskLevel.MEDIUM

    def test_default_score_when_missing(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel
        result = service._determine_churn_risk({})
        assert result == ChurnRiskLevel.MEDIUM


# ─── _determine_priority ────────────────────────────────────────────────────

class TestDeterminePriority:

    def test_high_urgency(self, service):
        from app.models.presale_follow_up_reminder import ReminderPriority
        result = service._determine_priority("high")
        assert result == ReminderPriority.HIGH

    def test_low_urgency(self, service):
        from app.models.presale_follow_up_reminder import ReminderPriority
        result = service._determine_priority("low")
        assert result == ReminderPriority.LOW

    def test_medium_urgency(self, service):
        from app.models.presale_follow_up_reminder import ReminderPriority
        result = service._determine_priority("medium")
        assert result == ReminderPriority.MEDIUM

    def test_unknown_urgency_defaults_to_medium(self, service):
        from app.models.presale_follow_up_reminder import ReminderPriority
        result = service._determine_priority("unknown")
        assert result == ReminderPriority.MEDIUM


# ─── _calculate_recommended_time ────────────────────────────────────────────

class TestCalculateRecommendedTime:

    def test_high_urgency_2_hours(self, service):
        before = datetime.now()
        result = service._calculate_recommended_time("high")
        after = datetime.now()
        delta = result - before
        assert timedelta(hours=1, minutes=55) <= delta <= timedelta(hours=2, minutes=5)

    def test_low_urgency_3_days(self, service):
        before = datetime.now()
        result = service._calculate_recommended_time("low")
        delta = result - before
        assert timedelta(days=2, hours=23) <= delta <= timedelta(days=3, hours=1)

    def test_medium_urgency_1_day(self, service):
        before = datetime.now()
        result = service._calculate_recommended_time("medium")
        delta = result - before
        assert timedelta(hours=23) <= delta <= timedelta(hours=25)


# ─── _identify_turning_points ───────────────────────────────────────────────

class TestIdentifyTurningPoints:

    def test_too_few_points_returns_empty(self, service):
        data = [
            {"date": "2025-01-01", "sentiment": "positive", "intent_score": 70},
            {"date": "2025-01-02", "sentiment": "positive", "intent_score": 80},
        ]
        result = service._identify_turning_points(data)
        assert result == []

    def test_peak_detected(self, service):
        data = [
            {"date": "2025-01-01", "sentiment": "positive", "intent_score": 60},
            {"date": "2025-01-02", "sentiment": "positive", "intent_score": 90},
            {"date": "2025-01-03", "sentiment": "positive", "intent_score": 70},
        ]
        result = service._identify_turning_points(data)
        assert len(result) == 1
        assert result[0]["type"] == "peak"

    def test_valley_detected(self, service):
        data = [
            {"date": "2025-01-01", "intent_score": 80, "sentiment": "positive"},
            {"date": "2025-01-02", "intent_score": 30, "sentiment": "negative"},
            {"date": "2025-01-03", "intent_score": 75, "sentiment": "positive"},
        ]
        result = service._identify_turning_points(data)
        assert len(result) == 1
        assert result[0]["type"] == "valley"

    def test_max_5_turning_points_returned(self, service):
        # Create many oscillations
        data = []
        for i in range(20):
            score = 90 if i % 2 == 0 else 30
            data.append({"date": f"2025-01-{i+1:02d}", "sentiment": "positive", "intent_score": score})
        result = service._identify_turning_points(data)
        assert len(result) <= 5


# ─── _needs_attention ───────────────────────────────────────────────────────

class TestNeedsAttention:

    def test_high_churn_needs_attention(self, service):
        assert service._needs_attention("positive", 50.0, "high") is True

    def test_negative_sentiment_needs_attention(self, service):
        assert service._needs_attention("negative", 50.0, "low") is True

    def test_high_intent_needs_attention(self, service):
        assert service._needs_attention("neutral", 85.0, "low") is True

    def test_normal_no_attention(self, service):
        assert service._needs_attention("neutral", 50.0, "low") is False

    def test_none_values_no_attention(self, service):
        assert service._needs_attention(None, None, None) is False


# ─── _recommend_action ──────────────────────────────────────────────────────

class TestRecommendAction:

    def test_high_churn_urgent(self, service):
        result = service._recommend_action("positive", 50.0, "high")
        assert "紧急" in result or "挽回" in result

    def test_high_intent_close_deal(self, service):
        result = service._recommend_action("positive", 85.0, "low")
        assert "促成" in result or "联系" in result

    def test_negative_sentiment_address_issue(self, service):
        result = service._recommend_action("negative", 40.0, "medium")
        assert "消极" in result or "问题" in result

    def test_default_action(self, service):
        result = service._recommend_action("neutral", 30.0, "low")
        assert isinstance(result, str) and len(result) > 0


# ─── _get_default_* ─────────────────────────────────────────────────────────

class TestDefaultResults:

    def test_default_emotion_result_structure(self, service):
        result = service._get_default_emotion_result()
        assert "sentiment_score" in result
        assert "purchase_intent_score" in result
        assert "churn_indicators" in result

    def test_default_churn_result_structure(self, service):
        result = service._get_default_churn_result()
        assert "risk_score" in result
        assert "retention_strategies" in result

    def test_default_follow_up_result_structure(self, service):
        result = service._get_default_follow_up_result()
        assert "urgency" in result
        assert "content" in result
        assert "reason" in result


# ─── batch_analyze_customers ────────────────────────────────────────────────

class TestBatchAnalyzeCustomers:

    @pytest.mark.asyncio
    async def test_empty_list(self, service):
        result = await service.batch_analyze_customers([])
        assert result["total_analyzed"] == 0
        assert result["success_count"] == 0

    @pytest.mark.asyncio
    async def test_customers_without_analysis(self, db_session):
        from app.services.ai_emotion_service import AIEmotionService
        svc = AIEmotionService(db_session)

        # No existing analyses
        db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = await svc.batch_analyze_customers([1, 2, 3])
        assert result["total_analyzed"] == 3
        assert result["success_count"] == 3

    @pytest.mark.asyncio
    async def test_customer_with_existing_analysis(self, db_session):
        from app.services.ai_emotion_service import AIEmotionService
        from app.models.presale_ai_emotion_analysis import SentimentType, ChurnRiskLevel
        svc = AIEmotionService(db_session)

        mock_analysis = MagicMock()
        mock_analysis.sentiment = SentimentType.POSITIVE
        mock_analysis.purchase_intent_score = Decimal("85.0")
        mock_analysis.churn_risk = ChurnRiskLevel.LOW

        db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_analysis

        result = await svc.batch_analyze_customers([42])
        assert result["success_count"] == 1
        summary = result["summaries"][0]
        assert summary["customer_id"] == 42
        assert summary["needs_attention"] is True  # High intent (85) triggers attention


# ─── get_follow_up_reminders ────────────────────────────────────────────────

class TestGetFollowUpReminders:

    def test_get_reminders_no_filter(self, db_session):
        from app.services.ai_emotion_service import AIEmotionService
        svc = AIEmotionService(db_session)

        mock_reminders = [MagicMock(), MagicMock()]
        q = db_session.query.return_value
        q.order_by.return_value.limit.return_value.all.return_value = mock_reminders

        result = svc.get_follow_up_reminders()
        assert len(result) == 2

    def test_dismiss_reminder_not_found(self, db_session):
        from app.services.ai_emotion_service import AIEmotionService
        svc = AIEmotionService(db_session)

        db_session.query.return_value.filter.return_value.first.return_value = None
        result = svc.dismiss_reminder(9999)
        assert result is False

    def test_dismiss_reminder_success(self, db_session):
        from app.services.ai_emotion_service import AIEmotionService
        from app.models.presale_follow_up_reminder import ReminderStatus
        svc = AIEmotionService(db_session)

        mock_reminder = MagicMock()
        db_session.query.return_value.filter.return_value.first.return_value = mock_reminder
        db_session.commit.return_value = None

        result = svc.dismiss_reminder(1)
        assert result is True
        assert mock_reminder.status == ReminderStatus.DISMISSED


# ─── AI call fallback (network errors) ──────────────────────────────────────

class TestOpenAIFallback:

    @pytest.mark.asyncio
    async def test_emotion_call_network_error_returns_default(self, service):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Network error")
            result = await service._call_openai_for_emotion("test content")
        # Should return default
        assert "sentiment_score" in result

    @pytest.mark.asyncio
    async def test_churn_call_non_200_returns_default(self, service):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            result = await service._call_openai_for_churn({"communications": []})
        assert "risk_score" in result

    @pytest.mark.asyncio
    async def test_follow_up_call_success(self, service):
        response_data = {"urgency": "high", "content": "跟进内容", "reason": "客户意向高"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(response_data)}}]
        }
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            result = await service._call_openai_for_follow_up({"sentiment": "positive"})
        assert result["urgency"] == "high"
