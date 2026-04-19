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


@pytest.fixture
def service():
    from app.services.ai_emotion_service import AIEmotionService

    return AIEmotionService(MagicMock())


class TestDetermineSentiment:
    def test_positive_score(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType

        assert service._determine_sentiment(50) == SentimentType.POSITIVE

    def test_negative_score(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType

        assert service._determine_sentiment(-50) == SentimentType.NEGATIVE

    def test_neutral_score_zero(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType

        assert service._determine_sentiment(0) == SentimentType.NEUTRAL

    def test_boundary_positive(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType

        assert service._determine_sentiment(31) == SentimentType.POSITIVE

    def test_boundary_negative(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType

        assert service._determine_sentiment(-31) == SentimentType.NEGATIVE

    def test_neutral_range(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType

        for score in [0, 10, -10, 29, -29]:
            assert service._determine_sentiment(score) == SentimentType.NEUTRAL


class TestDetermineChurnRisk:
    def test_high_risk(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel

        assert service._determine_churn_risk({"risk_score": 75}) == ChurnRiskLevel.HIGH

    def test_medium_risk(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel

        assert service._determine_churn_risk({"risk_score": 50}) == ChurnRiskLevel.MEDIUM

    def test_low_risk(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel

        assert service._determine_churn_risk({"risk_score": 20}) == ChurnRiskLevel.LOW

    def test_boundary_high(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel

        assert service._determine_churn_risk({"risk_score": 70}) == ChurnRiskLevel.HIGH

    def test_boundary_medium(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel

        assert service._determine_churn_risk({"risk_score": 40}) == ChurnRiskLevel.MEDIUM

    def test_default_score_when_missing(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel

        assert service._determine_churn_risk({}) == ChurnRiskLevel.MEDIUM


class TestDeterminePriority:
    def test_high_urgency(self, service):
        from app.models.presale_follow_up_reminder import ReminderPriority

        assert service._determine_priority("high") == ReminderPriority.HIGH

    def test_low_urgency(self, service):
        from app.models.presale_follow_up_reminder import ReminderPriority

        assert service._determine_priority("low") == ReminderPriority.LOW

    def test_medium_urgency(self, service):
        from app.models.presale_follow_up_reminder import ReminderPriority

        assert service._determine_priority("medium") == ReminderPriority.MEDIUM

    def test_unknown_urgency_defaults_to_medium(self, service):
        from app.models.presale_follow_up_reminder import ReminderPriority

        assert service._determine_priority("unknown") == ReminderPriority.MEDIUM


class TestCalculateRecommendedTime:
    def test_high_urgency_2_hours(self, service):
        before = datetime.now()
        result = service._calculate_recommended_time("high")
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


class TestIdentifyTurningPoints:
    def test_too_few_points_returns_empty(self, service):
        data = [
            {"date": "2025-01-01", "sentiment": "positive", "intent_score": 70},
            {"date": "2025-01-02", "sentiment": "positive", "intent_score": 80},
        ]
        assert service._identify_turning_points(data) == []

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
        data = []
        for i in range(20):
            score = 90 if i % 2 == 0 else 30
            data.append({"date": f"2025-01-{i+1:02d}", "sentiment": "positive", "intent_score": score})
        result = service._identify_turning_points(data)
        assert len(result) <= 5


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


class TestDefaultResults:
    def test_default_emotion_result_structure(self, service):
        result = service._get_default_emotion_result()
        assert "sentiment_score" in result
        assert "purchase_intent_score" in result


class TestBatchAnalyzeCustomers:
    @pytest.mark.asyncio
    async def test_empty_list(self, service):
        result = await service.batch_analyze_customers([])
        assert result["total_analyzed"] == 0
        assert result["success_count"] == 0

    @pytest.mark.asyncio
    async def test_customers_without_analysis(self):
        from app.services.ai_emotion_service import AIEmotionService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        svc = AIEmotionService(mock_db)

        result = await svc.batch_analyze_customers([1, 2, 3])
        assert result["total_analyzed"] == 3
        assert result["success_count"] == 3

    @pytest.mark.asyncio
    async def test_customer_with_existing_analysis(self):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel, SentimentType
        from app.services.ai_emotion_service import AIEmotionService

        mock_db = MagicMock()
        mock_analysis = MagicMock()
        mock_analysis.sentiment = SentimentType.POSITIVE
        mock_analysis.purchase_intent_score = Decimal("85.0")
        mock_analysis.churn_risk = ChurnRiskLevel.LOW
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_analysis
        svc = AIEmotionService(mock_db)

        result = await svc.batch_analyze_customers([42])
        assert result["success_count"] == 1
        summary = result["summaries"][0]
        assert summary["customer_id"] == 42
        assert summary["needs_attention"] is True


class TestGetFollowUpReminders:
    def test_get_reminders_no_filter(self):
        from app.services.ai_emotion_service import AIEmotionService

        mock_db = MagicMock()
        mock_reminders = [MagicMock(), MagicMock()]
        q = mock_db.query.return_value
        q.order_by.return_value.limit.return_value.all.return_value = mock_reminders
        svc = AIEmotionService(mock_db)

        result = svc.get_follow_up_reminders()
        assert len(result) == 2

    def test_dismiss_reminder_not_found(self):
        from app.services.ai_emotion_service import AIEmotionService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        svc = AIEmotionService(mock_db)

        result = svc.dismiss_reminder(9999)
        assert result is False

    def test_dismiss_reminder_success(self):
        from app.models.presale_follow_up_reminder import ReminderStatus
        from app.services.ai_emotion_service import AIEmotionService

        mock_db = MagicMock()
        mock_reminder = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_reminder
        svc = AIEmotionService(mock_db)

        result = svc.dismiss_reminder(1)
        assert result is True
        assert mock_reminder.status == ReminderStatus.DISMISSED


class TestOpenAIFallback:
    @pytest.mark.asyncio
    async def test_emotion_call_network_error_returns_default(self, service):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Network error")
            result = await service._call_openai_for_emotion("test content")
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
        mock_response.json.return_value = {"choices": [{"message": {"content": json.dumps(response_data)}}]}
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            result = await service._call_openai_for_follow_up({"sentiment": "positive"})
        assert result["urgency"] == "high"
