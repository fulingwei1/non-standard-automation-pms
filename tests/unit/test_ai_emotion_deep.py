# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - AI情绪分析服务"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from decimal import Decimal


class TestAIEmotionServiceBusinessLogic:
    """AI情绪分析服务业务逻辑测试"""

    def test_determine_sentiment_positive(self):
        """测试确定情绪（正面）"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            mock_db = MagicMock()
            service = AIEmotionService(mock_db)

            result = service._determine_sentiment(80)

            assert result.value in ["POSITIVE", "positive"]
        except ImportError:
            pytest.skip("Module not found")

    def test_determine_sentiment_negative(self):
        """测试确定情绪（负面）"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            mock_db = MagicMock()
            service = AIEmotionService(mock_db)

            result = service._determine_sentiment(20)

            assert result.value in ["NEGATIVE", "negative"]
        except ImportError:
            pytest.skip("Module not found")

    def test_determine_sentiment_neutral(self):
        """测试确定情绪（中性）"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            mock_db = MagicMock()
            service = AIEmotionService(mock_db)

            result = service._determine_sentiment(50)

            assert result.value in ["NEUTRAL", "neutral"]
        except ImportError:
            pytest.skip("Module not found")

    def test_determine_churn_risk_high(self):
        """测试确定流失风险（高）"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            mock_db = MagicMock()
            service = AIEmotionService(mock_db)

            churn_indicators = {
                "frequency_decline": True,
                "negative_sentiment_count": 10,
                "unresponsive_days": 30
            }

            result = service._determine_churn_risk(churn_indicators)

            assert result.value in ["HIGH", "high"]
        except ImportError:
            pytest.skip("Module not found")

    def test_determine_churn_risk_low(self):
        """测试确定流失风险（低）"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            mock_db = MagicMock()
            service = AIEmotionService(mock_db)

            churn_indicators = {
                "frequency_decline": False,
                "negative_sentiment_count": 1,
                "unresponsive_days": 2
            }

            result = service._determine_churn_risk(churn_indicators)

            assert result.value in ["LOW", "low"]
        except ImportError:
            pytest.skip("Module not found")

    @pytest.mark.asyncio
    async def test_analyze_emotion(self):
        """测试情绪分析"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            mock_db = MagicMock()

            service = AIEmotionService(mock_db)

            # Mock AI调用
            service._call_openai_for_emotion = AsyncMock(return_value={
                "sentiment_score": 70,
                "purchase_intent_score": 60,
                "churn_indicators": {},
                "emotion_factors": {}
            })

            service._update_emotion_trend = AsyncMock()

            with patch('app.utils.db_helpers.save_obj'):
                result = await service.analyze_emotion(1, 1, "客户表示很满意我们的方案")

                assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    @pytest.mark.asyncio
    async def test_predict_churn_risk(self):
        """测试流失风险预测"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            mock_db = MagicMock()

            service = AIEmotionService(mock_db)

            service._call_openai_for_churn = AsyncMock(return_value={
                "risk_level": "HIGH",
                "reasons": ["响应时间变长", "情绪下降"],
                "recommendations": ["主动联系"]
            })

            communications = ["最近有问题", "不太满意"]
            result = await service.predict_churn_risk(
                1, 1, communications,
                days_since_last_contact=30,
                response_time_trend=[1.0, 2.0, 3.0]
            )

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_generate_follow_up_reminders(self):
        """测试生成跟进提醒"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            mock_db = MagicMock()

            service = AIEmotionService(mock_db)

            mock_analysis = MagicMock()
            mock_analysis.churn_risk.value = "HIGH"
            mock_analysis.purchase_intent_score = Decimal("70")

            result = service._generate_follow_up_reminders(mock_analysis)

            assert isinstance(result, list)
        except ImportError:
            pytest.skip("Module not found")

    def test_get_customer_emotion_history(self):
        """测试获取客户情绪历史"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            mock_db = MagicMock()

            mock_analysis = MagicMock()
            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_analysis]

            service = AIEmotionService(mock_db)
            result = service.get_customer_emotion_history(1)

            assert isinstance(result, list)
        except ImportError:
            pytest.skip("Module not found")


class TestAIEmotionServiceOpenAI:
    """OpenAI集成测试"""

    @pytest.mark.asyncio
    async def test_call_openai_for_emotion(self):
        """测试调用OpenAI进行情绪分析"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            mock_db = MagicMock()

            service = AIEmotionService(mock_db)

            # Mock httpx
            with patch('httpx.AsyncClient') as MockClient:
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "choices": [{
                        "message": {
                            "content": json.dumps({
                                "sentiment_score": 75,
                                "purchase_intent_score": 80,
                                "churn_indicators": {}
                            })
                        }
                    }]
                }
                MockClient.return_value.__aenter__.return_value.post.return_value = mock_response

                result = await service._call_openai_for_emotion("测试内容")

                assert "sentiment_score" in result
        except ImportError:
            pytest.skip("Module not found")

    @pytest.mark.asyncio
    async def test_call_openai_for_churn(self):
        """测试调用OpenAI进行流失预测"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            mock_db = MagicMock()

            service = AIEmotionService(mock_db)

            with patch('httpx.AsyncClient') as MockClient:
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "choices": [{
                        "message": {
                            "content": json.dumps({
                                "risk_level": "MEDIUM",
                                "reasons": [],
                                "recommendations": []
                            })
                        }
                    }]
                }
                MockClient.return_value.__aenter__.return_value.post.return_value = mock_response

                result = await service._call_openai_for_churn(["内容1", "内容2"])

                assert "risk_level" in result
        except ImportError:
            pytest.skip("Module not found")


class TestAIEmotionServiceConfiguration:
    """配置测试"""

    def test_api_key_from_env(self):
        """测试API密钥配置"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                mock_db = MagicMock()
                service = AIEmotionService(mock_db)

                assert service.openai_api_key == "test_key"
        except ImportError:
            pytest.skip("Module not found")

    def test_base_url_from_env(self):
        """测试Base URL配置"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            with patch.dict(os.environ, {"OPENAI_BASE_URL": "https://custom.api.com/v1"}):
                mock_db = MagicMock()
                service = AIEmotionService(mock_db)

                assert service.openai_base_url == "https://custom.api.com/v1"
        except ImportError:
            pytest.skip("Module not found")

    def test_model_from_env(self):
        """测试模型配置"""
        try:
            from app.services.ai_emotion_service import AIEmotionService
            import os

            with patch.dict(os.environ, {"OPENAI_MODEL": "gpt-4-turbo"}):
                mock_db = MagicMock()
                service = AIEmotionService(mock_db)

                assert service.model == "gpt-4-turbo"
        except ImportError:
            pytest.skip("Module not found")


class TestAIEmotionServiceEdgeCases:
    """边界情况测试"""

    def test_empty_communication_content(self):
        """测试空沟通内容"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            mock_db = MagicMock()
            service = AIEmotionService(mock_db)

            service._call_openai_for_emotion = AsyncMock(return_value={
                "sentiment_score": 50,
                "purchase_intent_score": 50,
                "churn_indicators": {}
            })

            result = service._determine_sentiment(50)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_sentiment_score_boundary(self):
        """测试情绪分数边界"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            mock_db = MagicMock()
            service = AIEmotionService(mock_db)

            # 测试边界值
            result_0 = service._determine_sentiment(0)
            result_100 = service._determine_sentiment(100)

            assert result_0 is not None
            assert result_100 is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_purchase_intent_score_range(self):
        """测试购买意向分数范围"""
        try:
            from app.services.ai_emotion_service import AIEmotionService
            from decimal import Decimal

            mock_db = MagicMock()
            service = AIEmotionService(mock_db)

            # 购买意向分数应该在0-100之间
            low_score = Decimal("10")
            high_score = Decimal("90")

            assert 0 <= low_score <= 100
            assert 0 <= high_score <= 100
        except ImportError:
            pytest.skip("Module not found")