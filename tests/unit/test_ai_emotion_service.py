# -*- coding: utf-8 -*-
"""
I2组 - AI情绪分析服务 单元测试
覆盖: app/services/ai_emotion_service.py
"""
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    from app.services.ai_emotion_service import AIEmotionService
    return AIEmotionService(mock_db)


# ─── 纯计算方法 ───────────────────────────────────────────────────────────────

class TestDetermineSentiment:
    def test_positive_high(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType
        assert service._determine_sentiment(80) == SentimentType.POSITIVE

    def test_negative_low(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType
        assert service._determine_sentiment(-80) == SentimentType.NEGATIVE

    def test_neutral_zero(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType
        assert service._determine_sentiment(0) == SentimentType.NEUTRAL

    def test_neutral_boundary_low(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType
        assert service._determine_sentiment(30) == SentimentType.NEUTRAL

    def test_neutral_boundary_neg(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType
        assert service._determine_sentiment(-30) == SentimentType.NEUTRAL

    def test_positive_boundary(self, service):
        from app.models.presale_ai_emotion_analysis import SentimentType
        assert service._determine_sentiment(31) == SentimentType.POSITIVE


class TestDetermineChurnRisk:
    def test_high_risk(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel
        assert service._determine_churn_risk({'risk_score': 75}) == ChurnRiskLevel.HIGH

    def test_medium_risk(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel
        assert service._determine_churn_risk({'risk_score': 50}) == ChurnRiskLevel.MEDIUM

    def test_low_risk(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel
        assert service._determine_churn_risk({'risk_score': 20}) == ChurnRiskLevel.LOW

    def test_boundary_high(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel
        assert service._determine_churn_risk({'risk_score': 70}) == ChurnRiskLevel.HIGH

    def test_boundary_medium(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel
        assert service._determine_churn_risk({'risk_score': 40}) == ChurnRiskLevel.MEDIUM

    def test_default_score(self, service):
        from app.models.presale_ai_emotion_analysis import ChurnRiskLevel
        # 无 risk_score 键时默认 50 → MEDIUM
        assert service._determine_churn_risk({}) == ChurnRiskLevel.MEDIUM


class TestDeterminePriority:
    def test_high(self, service):
        from app.models.presale_follow_up_reminder import ReminderPriority
        assert service._determine_priority("high") == ReminderPriority.HIGH

    def test_low(self, service):
        from app.models.presale_follow_up_reminder import ReminderPriority
        assert service._determine_priority("low") == ReminderPriority.LOW

    def test_medium_default(self, service):
        from app.models.presale_follow_up_reminder import ReminderPriority
        assert service._determine_priority("medium") == ReminderPriority.MEDIUM

    def test_unknown_defaults_to_medium(self, service):
        from app.models.presale_follow_up_reminder import ReminderPriority
        assert service._determine_priority("unknown") == ReminderPriority.MEDIUM


class TestCalculateRecommendedTime:
    def test_high_urgency(self, service):
        before = datetime.now()
        result = service._calculate_recommended_time("high")
        expected = before + timedelta(hours=2)
        assert abs((result - expected).total_seconds()) < 2

    def test_low_urgency(self, service):
        before = datetime.now()
        result = service._calculate_recommended_time("low")
        expected = before + timedelta(days=3)
        assert abs((result - expected).total_seconds()) < 2

    def test_medium_urgency(self, service):
        before = datetime.now()
        result = service._calculate_recommended_time("medium")
        expected = before + timedelta(days=1)
        assert abs((result - expected).total_seconds()) < 2


class TestNeedsAttention:
    def test_high_churn_risk(self, service):
        assert service._needs_attention("positive", 60.0, "high") is True

    def test_negative_sentiment(self, service):
        assert service._needs_attention("negative", 60.0, "low") is True

    def test_high_intent_score(self, service):
        assert service._needs_attention("neutral", 85.0, "low") is True

    def test_no_attention_needed(self, service):
        assert service._needs_attention("positive", 60.0, "low") is False

    def test_none_values(self, service):
        assert service._needs_attention(None, None, None) is False


class TestRecommendAction:
    def test_high_churn(self, service):
        result = service._recommend_action("positive", 50.0, "high")
        assert "紧急" in result

    def test_high_intent(self, service):
        result = service._recommend_action("positive", 85.0, "low")
        assert "高意向" in result

    def test_negative_sentiment(self, service):
        result = service._recommend_action("negative", 50.0, "low")
        assert "消极" in result

    def test_positive_medium_intent(self, service):
        result = service._recommend_action("positive", 65.0, "low")
        assert result  # 有推荐内容

    def test_default(self, service):
        result = service._recommend_action(None, None, None)
        assert "正常" in result


class TestIdentifyTurningPoints:
    def test_peak_detection(self, service):
        trend_data = [
            {"date": "2024-01-01", "sentiment": "positive", "intent_score": 50},
            {"date": "2024-01-02", "sentiment": "positive", "intent_score": 90},
            {"date": "2024-01-03", "sentiment": "positive", "intent_score": 60},
        ]
        result = service._identify_turning_points(trend_data)
        assert len(result) == 1
        assert result[0]["type"] == "peak"

    def test_valley_detection(self, service):
        trend_data = [
            {"date": "2024-01-01", "sentiment": "positive", "intent_score": 80},
            {"date": "2024-01-02", "sentiment": "negative", "intent_score": 20},
            {"date": "2024-01-03", "sentiment": "positive", "intent_score": 70},
        ]
        result = service._identify_turning_points(trend_data)
        assert len(result) == 1
        assert result[0]["type"] == "valley"

    def test_too_short(self, service):
        trend_data = [
            {"date": "2024-01-01", "intent_score": 50},
            {"date": "2024-01-02", "intent_score": 70},
        ]
        result = service._identify_turning_points(trend_data)
        assert result == []

    def test_limits_to_five(self, service):
        # 生成 7 个交替波峰波谷
        trend_data = []
        for i in range(9):
            trend_data.append({
                "date": f"2024-01-{i+1:02d}",
                "sentiment": "neutral",
                "intent_score": 80 if i % 2 == 0 else 20,
            })
        result = service._identify_turning_points(trend_data)
        assert len(result) <= 5


class TestDefaultResults:
    def test_default_emotion_result(self, service):
        result = service._get_default_emotion_result()
        assert "sentiment_score" in result
        assert "purchase_intent_score" in result

    def test_default_churn_result(self, service):
        result = service._get_default_churn_result()
        assert "risk_score" in result

    def test_default_follow_up_result(self, service):
        result = service._get_default_follow_up_result()
        assert "urgency" in result
        assert "content" in result


# ─── get_emotion_trend ────────────────────────────────────────────────────────

class TestGetEmotionTrend:
    def test_returns_query_result(self, service, mock_db):
        mock_trend = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_trend
        result = service.get_emotion_trend(42)
        assert result == mock_trend

    def test_returns_none_if_not_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = service.get_emotion_trend(99)
        assert result is None


# ─── get_follow_up_reminders ──────────────────────────────────────────────────

class TestGetFollowUpReminders:
    def test_no_filter(self, service, mock_db):
        mock_reminders = [MagicMock(), MagicMock()]
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = mock_reminders
        result = service.get_follow_up_reminders()
        assert result == mock_reminders

    def test_with_status_and_priority(self, service, mock_db):
        mock_chain = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value = mock_chain
        mock_chain.order_by.return_value.limit.return_value.all.return_value = []
        result = service.get_follow_up_reminders(status="pending", priority="high")
        assert result == []


# ─── dismiss_reminder ─────────────────────────────────────────────────────────

class TestDismissReminder:
    def test_dismiss_existing(self, service, mock_db):
        from app.models.presale_follow_up_reminder import ReminderStatus
        mock_reminder = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_reminder
        result = service.dismiss_reminder(1)
        assert result is True
        assert mock_reminder.status == ReminderStatus.DISMISSED
        mock_db.commit.assert_called_once()

    def test_dismiss_not_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = service.dismiss_reminder(999)
        assert result is False


# ─── batch_analyze_customers ──────────────────────────────────────────────────

class TestBatchAnalyzeCustomers:
    @pytest.mark.asyncio
    async def test_basic_batch(self, service, mock_db):
        mock_analysis = MagicMock()
        mock_analysis.sentiment.value = "positive"
        mock_analysis.purchase_intent_score = Decimal("70")
        mock_analysis.churn_risk.value = "low"
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_analysis

        result = await service.batch_analyze_customers([1, 2])
        assert result["total_analyzed"] == 2
        assert result["success_count"] == 2
        assert result["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_no_analysis_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = await service.batch_analyze_customers([5, 6])
        assert result["total_analyzed"] == 2
        assert result["success_count"] == 2

    @pytest.mark.asyncio
    async def test_handles_exception(self, service, mock_db):
        mock_db.query.side_effect = Exception("DB error")
        result = await service.batch_analyze_customers([7])
        assert result["failed_count"] == 1


# ─── _call_openai_for_emotion (mock httpx) ────────────────────────────────────

class TestCallOpenAIForEmotion:
    @pytest.mark.asyncio
    async def test_success_response(self, service):
        fake_result = {
            "sentiment_score": 75,
            "purchase_intent_score": 80,
            "emotion_factors": {},
            "churn_indicators": {"risk_score": 20},
            "summary": "很好"
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(fake_result)}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await service._call_openai_for_emotion("客户沟通内容")
            assert result["sentiment_score"] == 75

    @pytest.mark.asyncio
    async def test_non_200_returns_default(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await service._call_openai_for_emotion("内容")
            assert result["sentiment_score"] == 0  # 默认值

    @pytest.mark.asyncio
    async def test_exception_returns_default(self, service):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=Exception("network error"))
            mock_client_cls.return_value = mock_client

            result = await service._call_openai_for_emotion("内容")
            assert "sentiment_score" in result

    @pytest.mark.asyncio
    async def test_invalid_json_returns_default(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "不是JSON"}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await service._call_openai_for_emotion("内容")
            assert result["sentiment_score"] == 0

    @pytest.mark.asyncio
    async def test_markdown_json_response(self, service):
        fake_result = {"sentiment_score": 60, "purchase_intent_score": 70,
                       "emotion_factors": {}, "churn_indicators": {"risk_score": 30},
                       "summary": "ok"}
        markdown_content = f"```json\n{json.dumps(fake_result)}\n```"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": markdown_content}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await service._call_openai_for_emotion("内容")
            assert result["sentiment_score"] == 60


# ─── analyze_emotion ─────────────────────────────────────────────────────────

class TestAnalyzeEmotion:
    @pytest.mark.asyncio
    async def test_analyze_emotion_success(self, service, mock_db):
        fake_ai_result = {
            "sentiment_score": 70,
            "purchase_intent_score": 75,
            "emotion_factors": {"positive": ["好"]},
            "churn_indicators": {"risk_score": 15},
            "summary": "积极"
        }

        with patch.object(service, "_call_openai_for_emotion", new_callable=AsyncMock) as mock_ai, \
             patch.object(service, "_update_emotion_trend", new_callable=AsyncMock) as mock_trend, \
             patch("app.services.ai_emotion_service.save_obj") as mock_save:
            mock_ai.return_value = fake_ai_result

            result = await service.analyze_emotion(1, 2, "客户说很感兴趣")
            assert mock_ai.called
            assert mock_save.called
            assert mock_trend.called


# ─── predict_churn_risk ───────────────────────────────────────────────────────

class TestPredictChurnRisk:
    @pytest.mark.asyncio
    async def test_predict_churn_risk(self, service):
        fake_churn = {
            "risk_score": 60,
            "risk_factors": ["长时间未联系"],
            "retention_strategies": ["及时跟进"],
            "summary": "风险较高"
        }
        with patch.object(service, "_call_openai_for_churn", new_callable=AsyncMock) as mock_churn:
            mock_churn.return_value = fake_churn
            result = await service.predict_churn_risk(
                presale_ticket_id=1,
                customer_id=2,
                recent_communications=["沟通1", "沟通2"],
                days_since_last_contact=7,
            )
            assert result["presale_ticket_id"] == 1
            assert result["risk_score"] == 60
            assert "risk_factors" in result


# ─── recommend_follow_up ──────────────────────────────────────────────────────

class TestRecommendFollowUp:
    @pytest.mark.asyncio
    async def test_recommend_with_emotion_id(self, service, mock_db):
        mock_emotion = MagicMock()
        mock_emotion.sentiment.value = "positive"
        mock_emotion.purchase_intent_score = Decimal("70")
        mock_emotion.churn_risk.value = "low"
        mock_emotion.emotion_factors = {}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_emotion

        fake_follow_up = {"urgency": "medium", "content": "跟进内容", "reason": "原因"}

        with patch.object(service, "_call_openai_for_follow_up", new_callable=AsyncMock) as mock_fu, \
             patch("app.services.ai_emotion_service.save_obj") as mock_save:
            mock_fu.return_value = fake_follow_up
            result = await service.recommend_follow_up(1, 2, latest_emotion_analysis_id=10)
            assert mock_save.called

    @pytest.mark.asyncio
    async def test_recommend_without_emotion(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        fake_follow_up = {"urgency": "low", "content": "保持联系", "reason": "常规"}

        with patch.object(service, "_call_openai_for_follow_up", new_callable=AsyncMock) as mock_fu, \
             patch("app.services.ai_emotion_service.save_obj") as mock_save:
            mock_fu.return_value = fake_follow_up
            result = await service.recommend_follow_up(1, 2)
            assert mock_save.called
